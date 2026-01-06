"""
Query Audit Logger
Logs all SQL queries for security and debugging.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class QueryLog:
    """Represents a logged query"""
    timestamp: str
    query: str
    status: str  # 'approved', 'rejected', 'error'
    execution_time_ms: Optional[float] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    warnings: Optional[list] = None
    modified_query: Optional[str] = None


class QueryAuditor:
    """Audits and logs all SQL queries"""
    
    def __init__(self, audit_db_path: str = "data/processed/query_audit.db"):
        """
        Initialize auditor with SQLite database for logs
        
        Args:
            audit_db_path: Path to audit log database
        """
        self.audit_db_path = audit_db_path
        
        # Ensure directory exists
        Path(audit_db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize audit database
        self._init_audit_db()
    
    def _init_audit_db(self):
        """Create audit log table if it doesn't exist"""
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_time_ms REAL,
                row_count INTEGER,
                error_message TEXT,
                warnings TEXT,
                modified_query TEXT
            )
        """)
        
        # Create index on timestamp for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON query_logs(timestamp)
        """)
        
        # Create index on status for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON query_logs(status)
        """)
        
        conn.commit()
        conn.close()
    
    def log_query(self, query_log: QueryLog):
        """
        Log a query to the audit database
        
        Args:
            query_log: QueryLog object to store
        """
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        # Convert warnings list to JSON string
        warnings_json = json.dumps(query_log.warnings) if query_log.warnings else None
        
        cursor.execute("""
            INSERT INTO query_logs 
            (timestamp, query, status, execution_time_ms, row_count, 
             error_message, warnings, modified_query)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            query_log.timestamp,
            query_log.query,
            query_log.status,
            query_log.execution_time_ms,
            query_log.row_count,
            query_log.error_message,
            warnings_json,
            query_log.modified_query
        ))
        
        conn.commit()
        conn.close()
    
    def log_approved(self, query: str, execution_time_ms: float, 
                     row_count: int, warnings: list = None, 
                     modified_query: str = None):
        """Log an approved and executed query"""
        query_log = QueryLog(
            timestamp=datetime.now().isoformat(),
            query=query,
            status='approved',
            execution_time_ms=execution_time_ms,
            row_count=row_count,
            warnings=warnings,
            modified_query=modified_query
        )
        self.log_query(query_log)
    
    def log_rejected(self, query: str, error_message: str):
        """Log a rejected query"""
        query_log = QueryLog(
            timestamp=datetime.now().isoformat(),
            query=query,
            status='rejected',
            error_message=error_message
        )
        self.log_query(query_log)
    
    def log_error(self, query: str, error_message: str):
        """Log a query that caused an execution error"""
        query_log = QueryLog(
            timestamp=datetime.now().isoformat(),
            query=query,
            status='error',
            error_message=error_message
        )
        self.log_query(query_log)
    
    def get_recent_logs(self, limit: int = 10, status_filter: str = None) -> list:
        """
        Get recent query logs
        
        Args:
            limit: Maximum number of logs to return
            status_filter: Filter by status ('approved', 'rejected', 'error')
            
        Returns:
            List of query log dictionaries
        """
        conn = sqlite3.connect(self.audit_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status_filter:
            query = """
                SELECT * FROM query_logs 
                WHERE status = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            cursor.execute(query, (status_filter, limit))
        else:
            query = """
                SELECT * FROM query_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            cursor.execute(query, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        logs = []
        for row in rows:
            log_dict = dict(row)
            # Parse warnings JSON back to list
            if log_dict['warnings']:
                log_dict['warnings'] = json.loads(log_dict['warnings'])
            logs.append(log_dict)
        
        return logs
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        # Total queries by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM query_logs
            GROUP BY status
        """)
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average execution time for approved queries
        cursor.execute("""
            SELECT AVG(execution_time_ms) as avg_time
            FROM query_logs
            WHERE status = 'approved' AND execution_time_ms IS NOT NULL
        """)
        avg_exec_time = cursor.fetchone()[0] or 0
        
        # Total rows returned
        cursor.execute("""
            SELECT SUM(row_count) as total_rows
            FROM query_logs
            WHERE status = 'approved'
        """)
        total_rows = cursor.fetchone()[0] or 0
        
        # Most common errors
        cursor.execute("""
            SELECT error_message, COUNT(*) as count
            FROM query_logs
            WHERE status IN ('rejected', 'error')
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 5
        """)
        common_errors = [
            {'error': row[0], 'count': row[1]} 
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'total_queries': sum(status_counts.values()),
            'approved': status_counts.get('approved', 0),
            'rejected': status_counts.get('rejected', 0),
            'errors': status_counts.get('error', 0),
            'avg_execution_time_ms': round(avg_exec_time, 2),
            'total_rows_returned': total_rows,
            'common_errors': common_errors
        }
    
    def clear_old_logs(self, days: int = 30):
        """Delete logs older than specified days"""
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM query_logs
            WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
        """, (days,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
