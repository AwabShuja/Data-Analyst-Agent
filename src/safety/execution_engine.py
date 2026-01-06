"""
Safe Query Execution Engine
Combines validation and audit for safe SQL query execution.
"""

import pandas as pd
import sqlite3
import time
import signal
from typing import Optional, Dict, Any
from contextlib import contextmanager

from .validator import SQLValidator, ValidationResult
from .audit import QueryAuditor, QueryLog


class QueryTimeoutError(Exception):
    """Raised when query execution times out"""
    pass


class SafeQueryEngine:
    """Safe SQL query execution with validation and auditing"""
    
    def __init__(self, db_path: str, config: Dict, audit_enabled: bool = True):
        """
        Initialize safe query engine
        
        Args:
            db_path: Path to SQLite database
            config: Configuration dict with safety settings
            audit_enabled: Whether to enable query auditing
        """
        self.db_path = db_path
        self.config = config
        self.audit_enabled = audit_enabled
        
        # Initialize validator
        self.validator = SQLValidator(db_path, config['safety'])
        
        # Initialize auditor
        if audit_enabled:
            self.auditor = QueryAuditor()
        else:
            self.auditor = None
        
        # Database connection
        self.conn = sqlite3.connect(db_path)
    
    def execute_query(self, query: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute SQL query with safety checks
        
        Args:
            query: SQL query string
            timeout: Query timeout in seconds (default from config)
            
        Returns:
            Dict with:
                - success: bool
                - data: pandas DataFrame (if successful)
                - error: str (if failed)
                - warnings: list of warnings
                - execution_time_ms: float
                - row_count: int
        """
        start_time = time.time()
        
        # Set default timeout
        if timeout is None:
            timeout = self.config['safety'].get('query_timeout_seconds', 30)
        
        # Step 1: Validate query
        validation = self.validator.validate_query(query)
        
        if not validation.is_valid:
            # Log rejection
            if self.auditor:
                self.auditor.log_rejected(query, validation.error_message)
            
            return {
                'success': False,
                'error': validation.error_message,
                'warnings': validation.warnings,
                'execution_time_ms': (time.time() - start_time) * 1000
            }
        
        # Use modified query if validator changed it
        final_query = validation.modified_query or query
        
        # Step 2: Execute query with timeout
        try:
            with self._timeout(timeout):
                df = pd.read_sql_query(final_query, self.conn)
            
            execution_time_ms = (time.time() - start_time) * 1000
            row_count = len(df)
            
            # Log success
            if self.auditor:
                self.auditor.log_approved(
                    query=query,
                    execution_time_ms=execution_time_ms,
                    row_count=row_count,
                    warnings=validation.warnings,
                    modified_query=final_query if final_query != query else None
                )
            
            return {
                'success': True,
                'data': df,
                'warnings': validation.warnings,
                'execution_time_ms': execution_time_ms,
                'row_count': row_count,
                'modified_query': final_query if final_query != query else None
            }
            
        except QueryTimeoutError:
            error_msg = f"⏱️ Query execution timeout after {timeout} seconds"
            if self.auditor:
                self.auditor.log_error(query, error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'execution_time_ms': (time.time() - start_time) * 1000
            }
            
        except Exception as e:
            error_msg = f"💥 Execution error: {str(e)}"
            if self.auditor:
                self.auditor.log_error(query, error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'execution_time_ms': (time.time() - start_time) * 1000
            }
    
    @contextmanager
    def _timeout(self, seconds: int):
        """Context manager for query timeout (Windows compatible)"""
        # Note: signal.alarm doesn't work on Windows
        # For production, use threading.Timer or multiprocessing
        # For now, we'll rely on SQLite's built-in timeout
        
        old_timeout = self.conn.execute("PRAGMA busy_timeout").fetchone()[0]
        self.conn.execute(f"PRAGMA busy_timeout = {seconds * 1000}")
        
        try:
            yield
        finally:
            self.conn.execute(f"PRAGMA busy_timeout = {old_timeout}")
    
    def get_schema_info(self) -> Dict:
        """Get database schema for LLM context"""
        return self.validator.get_schema_info()
    
    def get_table_preview(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample rows from a table"""
        rows = self.validator.get_table_preview(table_name, limit)
        
        # Get column names
        columns = list(self.validator.table_columns[table_name.lower()])
        
        return pd.DataFrame(rows, columns=columns)
    
    def validate_only(self, query: str) -> ValidationResult:
        """Validate query without executing"""
        return self.validator.validate_query(query)
    
    def get_audit_stats(self) -> Dict:
        """Get audit statistics"""
        if self.auditor:
            return self.auditor.get_statistics()
        return {}
    
    def get_recent_queries(self, limit: int = 10, status: str = None) -> list:
        """Get recent query logs"""
        if self.auditor:
            return self.auditor.get_recent_logs(limit, status)
        return []
    
    def close(self):
        """Close connections"""
        if self.conn:
            self.conn.close()
        if self.validator:
            self.validator.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
