"""
SQL Query Validator
Validates SQL queries for safety before execution.
"""

import re
import sqlite3
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of SQL validation"""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    modified_query: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class SQLValidator:
    """Validates SQL queries for safety and correctness"""
    
    def __init__(self, db_path: str, config: Dict):
        """
        Initialize validator with database connection and config
        
        Args:
            db_path: Path to SQLite database
            config: Configuration dict with safety settings
        """
        self.db_path = db_path
        self.config = config
        # check_same_thread=False for Streamlit compatibility
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Load tables and columns from database
        self._load_schema()
    
    def _load_schema(self):
        """Load database schema information"""
        # Get all tables
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        self.tables = {row[0].lower() for row in self.cursor.fetchall()}
        
        # Get columns for each table
        self.table_columns = {}
        for table in self.tables:
            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1].lower() for row in self.cursor.fetchall()]
            self.table_columns[table] = set(columns)
        
        # Get row counts for tables
        self.table_row_counts = {}
        for table in self.tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            self.table_row_counts[table] = self.cursor.fetchone()[0]
    
    def validate_query(self, query: str) -> ValidationResult:
        """
        Validate SQL query for safety
        
        Args:
            query: SQL query string
            
        Returns:
            ValidationResult with validation outcome
        """
        query = query.strip()
        query_upper = query.upper()
        warnings = []
        
        # 1. Check for dangerous keywords
        dangerous_keywords = self.config.get('dangerous_keywords', [
            'DELETE', 'DROP', 'UPDATE', 'INSERT', 'ALTER', 
            'CREATE', 'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE'
        ])
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', query_upper):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"🚫 Dangerous operation detected: {keyword}. Only SELECT queries are allowed."
                )
        
        # 2. Check if it's a SELECT query
        if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
            return ValidationResult(
                is_valid=False,
                error_message="🚫 Only SELECT queries are allowed. Query must start with SELECT or WITH."
            )
        
        # 3. Check for LIMIT clause
        max_rows = self.config.get('max_rows', 10000)
        has_limit = bool(re.search(r'\bLIMIT\s+\d+', query_upper))
        
        if not has_limit:
            warnings.append(f"⚠️ No LIMIT clause found. Adding LIMIT {max_rows} for safety.")
            # Add LIMIT to query
            if query.rstrip().endswith(';'):
                modified_query = query.rstrip()[:-1] + f" LIMIT {max_rows};"
            else:
                modified_query = query + f" LIMIT {max_rows}"
        else:
            # Check if limit is too high
            limit_match = re.search(r'\bLIMIT\s+(\d+)', query_upper)
            if limit_match:
                limit_value = int(limit_match.group(1))
                if limit_value > max_rows:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"🚫 LIMIT {limit_value} exceeds maximum allowed ({max_rows})"
                    )
            modified_query = query
        
        # 4. Validate table names exist
        tables_in_query = self._extract_table_names(query)
        invalid_tables = [t for t in tables_in_query if t not in self.tables]
        
        if invalid_tables:
            return ValidationResult(
                is_valid=False,
                error_message=f"🚫 Invalid table(s): {', '.join(invalid_tables)}. Available tables: {', '.join(sorted(self.tables))}"
            )
        
        # 5. Check for WHERE clause on large tables
        large_tables = self.config.get('require_where_tables', ['orders'])
        tables_needing_where = [t for t in tables_in_query if t in large_tables]
        
        if tables_needing_where:
            has_where = bool(re.search(r'\bWHERE\b', query_upper))
            has_join = bool(re.search(r'\bJOIN\b', query_upper))
            has_group = bool(re.search(r'\bGROUP BY\b', query_upper))
            
            # Allow queries with WHERE, or aggregations with GROUP BY
            if not (has_where or has_group):
                warnings.append(
                    f"⚠️ Querying large table(s) {', '.join(tables_needing_where)} without WHERE/GROUP BY. "
                    f"This may be slow."
                )
        
        # 6. Validate column names (basic check)
        columns_in_query = self._extract_column_references(query)
        for table, columns in columns_in_query.items():
            if table in self.table_columns:
                invalid_cols = [c for c in columns if c not in self.table_columns[table] and c != '*']
                if invalid_cols:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"🚫 Invalid column(s) in table '{table}': {', '.join(invalid_cols)}"
                    )
        
        # 7. Test query syntax by preparing it
        try:
            self.cursor.execute(f"EXPLAIN QUERY PLAN {modified_query}")
        except sqlite3.Error as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"🚫 SQL syntax error: {str(e)}"
            )
        
        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            modified_query=modified_query
        )
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from SQL query"""
        query_upper = query.upper()
        tables = []
        
        # Match FROM and JOIN clauses
        patterns = [
            r'\bFROM\s+(\w+)',
            r'\bJOIN\s+(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query_upper)
            tables.extend(matches)
        
        return [t.lower() for t in tables]
    
    def _extract_column_references(self, query: str) -> Dict[str, List[str]]:
        """
        Extract column references from query
        Returns dict of {table_name: [columns]}
        """
        column_refs = {}
        
        # Look for table.column patterns
        pattern = r'\b(\w+)\.(\w+)\b'
        matches = re.findall(pattern, query.lower())
        
        for table, column in matches:
            if table in self.tables:
                if table not in column_refs:
                    column_refs[table] = []
                column_refs[table].append(column)
        
        return column_refs
    
    def get_schema_info(self) -> Dict:
        """Get database schema information for LLM context"""
        schema_info = {
            'tables': {},
            'total_rows': sum(self.table_row_counts.values())
        }
        
        for table in sorted(self.tables):
            schema_info['tables'][table] = {
                'columns': sorted(list(self.table_columns[table])),
                'row_count': self.table_row_counts[table]
            }
        
        return schema_info
    
    def get_table_preview(self, table_name: str, limit: int = 5) -> List[Tuple]:
        """Get sample rows from a table"""
        table_name = table_name.lower()
        
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        
        query = f"SELECT * FROM {table_name} LIMIT {min(limit, 10)}"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
