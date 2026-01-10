"""
Metrics Tracker for monitoring agent performance over time.
Stores metrics in SQLite database for historical analysis.
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class MetricsTracker:
    """
    Tracks and stores agent evaluation metrics over time.
    Enables comparison between different runs and configurations.
    """
    
    def __init__(self, db_path: str = "data/processed/metrics.db"):
        """
        Initialize metrics tracker.
        
        Args:
            db_path: Path to SQLite database for storing metrics
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Create metrics tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Evaluation runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT,
                    temperature REAL,
                    max_retries INTEGER,
                    total_questions INTEGER,
                    successful INTEGER,
                    failed INTEGER,
                    success_rate REAL,
                    pattern_match_rate REAL,
                    total_retries INTEGER,
                    avg_retries_per_query REAL,
                    avg_execution_time_ms REAL,
                    avg_total_time_ms REAL,
                    total_evaluation_time_ms REAL,
                    notes TEXT
                )
            """)
            
            # Individual question results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS question_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    question_id INTEGER,
                    question TEXT,
                    difficulty TEXT,
                    category TEXT,
                    success INTEGER,
                    sql_generated TEXT,
                    pattern_match_rate REAL,
                    retries INTEGER,
                    execution_time_ms REAL,
                    total_time_ms REAL,
                    error TEXT,
                    result_count INTEGER,
                    timestamp TEXT,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id)
                )
            """)
            
            conn.commit()
    
    def save_run(
        self, 
        results: List[Dict[str, Any]], 
        metrics: Dict[str, Any],
        agent_config: Dict[str, Any],
        notes: str = ""
    ) -> int:
        """
        Save evaluation run to database.
        
        Args:
            results: List of individual question results
            metrics: Computed metrics from evaluator
            agent_config: Agent configuration
            notes: Optional notes about this run
            
        Returns:
            run_id of saved run
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert run metadata
            cursor.execute("""
                INSERT INTO evaluation_runs (
                    timestamp, model, temperature, max_retries,
                    total_questions, successful, failed, success_rate,
                    pattern_match_rate, total_retries, avg_retries_per_query,
                    avg_execution_time_ms, avg_total_time_ms, 
                    total_evaluation_time_ms, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                agent_config.get("model", "unknown"),
                agent_config.get("temperature", 0.1),
                agent_config.get("max_retries", 2),
                metrics["overall"]["total_questions"],
                metrics["overall"]["successful"],
                metrics["overall"]["failed"],
                float(metrics["overall"]["success_rate"].rstrip('%')),
                float(metrics["overall"]["pattern_match_rate"].rstrip('%')),
                metrics["self_correction"]["total_retries"],
                metrics["self_correction"]["avg_retries_per_query"],
                metrics["performance"]["avg_execution_time_ms"],
                metrics["performance"]["avg_total_time_ms"],
                metrics["performance"]["total_evaluation_time_ms"],
                notes
            ))
            
            run_id = cursor.lastrowid
            
            # Insert individual results
            for result in results:
                cursor.execute("""
                    INSERT INTO question_results (
                        run_id, question_id, question, difficulty, category,
                        success, sql_generated, pattern_match_rate, retries,
                        execution_time_ms, total_time_ms, error, result_count,
                        timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    result["question_id"],
                    result["question"],
                    result["difficulty"],
                    result["category"],
                    1 if result["success"] else 0,
                    result["sql_generated"],
                    result["pattern_match"]["match_rate"],
                    result["retries"],
                    result["execution_time_ms"],
                    result["total_time_ms"],
                    result.get("error", ""),
                    result["result_count"],
                    result["timestamp"]
                ))
            
            conn.commit()
            
        return run_id
    
    def get_run(self, run_id: int) -> Dict[str, Any]:
        """Get specific evaluation run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM evaluation_runs WHERE run_id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Get all evaluation runs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM evaluation_runs ORDER BY timestamp DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def compare_runs(self, run_id1: int, run_id2: int) -> Dict[str, Any]:
        """
        Compare two evaluation runs.
        
        Args:
            run_id1: First run ID
            run_id2: Second run ID
            
        Returns:
            Comparison dict
        """
        run1 = self.get_run(run_id1)
        run2 = self.get_run(run_id2)
        
        if not run1 or not run2:
            return {"error": "One or both runs not found"}
        
        def calculate_change(val1, val2):
            if val1 == 0:
                return float('inf') if val2 > 0 else 0
            return ((val2 - val1) / val1) * 100
        
        return {
            "run1": {
                "run_id": run_id1,
                "timestamp": run1["timestamp"],
                "model": run1["model"],
                "success_rate": run1["success_rate"]
            },
            "run2": {
                "run_id": run_id2,
                "timestamp": run2["timestamp"],
                "model": run2["model"],
                "success_rate": run2["success_rate"]
            },
            "changes": {
                "success_rate": {
                    "run1": run1["success_rate"],
                    "run2": run2["success_rate"],
                    "change_pct": round(calculate_change(run1["success_rate"], run2["success_rate"]), 2)
                },
                "pattern_match_rate": {
                    "run1": run1["pattern_match_rate"],
                    "run2": run2["pattern_match_rate"],
                    "change_pct": round(calculate_change(run1["pattern_match_rate"], run2["pattern_match_rate"]), 2)
                },
                "avg_execution_time_ms": {
                    "run1": run1["avg_execution_time_ms"],
                    "run2": run2["avg_execution_time_ms"],
                    "change_pct": round(calculate_change(run1["avg_execution_time_ms"], run2["avg_execution_time_ms"]), 2)
                },
                "avg_retries_per_query": {
                    "run1": run1["avg_retries_per_query"],
                    "run2": run2["avg_retries_per_query"],
                    "change_pct": round(calculate_change(run1["avg_retries_per_query"], run2["avg_retries_per_query"]), 2)
                }
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics across all runs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    AVG(success_rate) as avg_success_rate,
                    MAX(success_rate) as best_success_rate,
                    MIN(success_rate) as worst_success_rate,
                    AVG(avg_execution_time_ms) as avg_exec_time,
                    SUM(total_questions) as total_questions_evaluated
                FROM evaluation_runs
            """)
            
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            
            return dict(zip(columns, row))
    
    def get_trend(self, metric: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trend for a specific metric over recent runs.
        
        Args:
            metric: Metric name (success_rate, avg_execution_time_ms, etc.)
            limit: Number of recent runs to include
            
        Returns:
            List of {timestamp, value} dicts
        """
        valid_metrics = [
            "success_rate", "pattern_match_rate", "avg_execution_time_ms",
            "avg_total_time_ms", "avg_retries_per_query"
        ]
        
        if metric not in valid_metrics:
            return {"error": f"Invalid metric. Choose from: {valid_metrics}"}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT timestamp, {metric} as value
                FROM evaluation_runs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [{"timestamp": row[0], "value": row[1]} for row in cursor.fetchall()]
