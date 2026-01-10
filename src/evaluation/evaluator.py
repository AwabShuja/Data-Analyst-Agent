"""
Auto-Evaluator for SQL Agent.
Runs test questions and evaluates agent performance.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.test_questions import TestQuestions
from agent.sql_agent import SQLAgent


class AgentEvaluator:
    """
    Evaluates SQL agent performance on test questions.
    
    Features:
    - Runs all or subset of test questions
    - Validates SQL patterns in generated queries
    - Tracks success/failure metrics
    - Measures latency and self-correction rates
    - Generates detailed evaluation reports
    """
    
    def __init__(self, agent: SQLAgent):
        """
        Initialize evaluator.
        
        Args:
            agent: SQLAgent instance to evaluate
        """
        self.agent = agent
        self.results: List[Dict[str, Any]] = []
    
    def evaluate_single(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate agent on a single question.
        
        Args:
            question: Question dict from TestQuestions
            
        Returns:
            Evaluation result dict
        """
        start_time = datetime.now()
        
        # Ask agent
        response = self.agent.ask(question["question"])
        
        end_time = datetime.now()
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Validate SQL patterns
        sql_query = response.get("sql_query") or ""
        pattern_match = self._validate_patterns(
            sql_query,
            question["expected_patterns"]
        )
        
        # Compile result
        # Handle results - can be DataFrame or None
        results = response.get("results")
        if results is not None:
            try:
                result_count = len(results)
            except TypeError:
                result_count = 0
        else:
            result_count = 0
        
        result = {
            "question_id": question["id"],
            "question": question["question"],
            "difficulty": question["difficulty"],
            "category": question["category"],
            "success": response["success"],
            "sql_generated": sql_query,
            "pattern_match": pattern_match,
            "retries": response.get("retries", 0),
            "execution_time_ms": response.get("execution_time_ms", 0),
            "total_time_ms": round(total_time_ms, 2),
            "error": response.get("error", None),
            "result_count": result_count,
            "interpretation": response.get("interpretation", ""),
            "timestamp": start_time.isoformat()
        }
        
        return result
    
    def _validate_patterns(self, sql: str, expected_patterns: List[str]) -> Dict[str, Any]:
        """
        Validate that SQL contains expected patterns.
        
        Args:
            sql: Generated SQL query (can be empty string)
            expected_patterns: List of expected keywords/patterns
            
        Returns:
            Dict with validation results
        """
        # Handle None or empty SQL
        if not sql:
            return {
                "matched": [],
                "missing": expected_patterns,
                "match_rate": 0.0,
                "all_matched": False
            }
        
        sql_upper = sql.upper()
        
        matched = []
        missing = []
        
        for pattern in expected_patterns:
            pattern_upper = pattern.upper()
            if pattern_upper in sql_upper:
                matched.append(pattern)
            else:
                missing.append(pattern)
        
        match_rate = len(matched) / len(expected_patterns) if expected_patterns else 1.0
        
        return {
            "matched": matched,
            "missing": missing,
            "match_rate": round(match_rate, 2),
            "all_matched": len(missing) == 0
        }
    
    def evaluate_all(
        self, 
        difficulty: Optional[str] = None,
        max_questions: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate agent on all or subset of test questions.
        
        Args:
            difficulty: Filter by difficulty (easy/medium/hard), None for all
            max_questions: Maximum number of questions to evaluate
            
        Returns:
            List of evaluation results
        """
        # Get questions
        if difficulty:
            questions = TestQuestions.get_by_difficulty(difficulty)
        else:
            questions = TestQuestions.get_all_questions()
        
        if max_questions:
            questions = questions[:max_questions]
        
        print(f"\n{'='*70}")
        print(f"EVALUATING AGENT ON {len(questions)} QUESTIONS")
        print(f"{'='*70}\n")
        
        # Clear agent history
        self.agent.clear_history()
        
        # Evaluate each question
        results = []
        for i, question in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] {question['difficulty'].upper()}: {question['question']}")
            
            result = self.evaluate_single(question)
            results.append(result)
            
            # Print result
            status = "✅" if result["success"] else "❌"
            pattern_status = "✓" if result["pattern_match"]["all_matched"] else "⚠"
            print(f"  {status} Success | {pattern_status} Patterns ({result['pattern_match']['match_rate']*100:.0f}%) | "
                  f"⚡ {result['total_time_ms']:.0f}ms | 🔄 {result['retries']} retries")
            
            if not result["success"]:
                print(f"  ❌ Error: {result['error']}")
            elif not result["pattern_match"]["all_matched"]:
                print(f"  ⚠ Missing patterns: {', '.join(result['pattern_match']['missing'])}")
            
            print()
        
        self.results = results
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Calculate evaluation metrics from results.
        
        Returns:
            Dict with comprehensive metrics
        """
        if not self.results:
            return {"error": "No results available. Run evaluate_all() first."}
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        # Pattern matching
        pattern_matched = sum(1 for r in self.results if r["pattern_match"]["all_matched"])
        
        # Retries
        total_retries = sum(r["retries"] for r in self.results)
        queries_with_retries = sum(1 for r in self.results if r["retries"] > 0)
        
        # Timing
        avg_execution_time = sum(r["execution_time_ms"] for r in self.results if r["success"]) / successful if successful > 0 else 0
        avg_total_time = sum(r["total_time_ms"] for r in self.results) / total
        
        # By difficulty
        by_difficulty = {}
        for difficulty in ["easy", "medium", "hard"]:
            diff_results = [r for r in self.results if r["difficulty"] == difficulty]
            if diff_results:
                diff_successful = sum(1 for r in diff_results if r["success"])
                by_difficulty[difficulty] = {
                    "total": len(diff_results),
                    "successful": diff_successful,
                    "success_rate": f"{(diff_successful/len(diff_results)*100):.1f}%"
                }
        
        # By category
        categories = set(r["category"] for r in self.results)
        by_category = {}
        for category in categories:
            cat_results = [r for r in self.results if r["category"] == category]
            cat_successful = sum(1 for r in cat_results if r["success"])
            by_category[category] = {
                "total": len(cat_results),
                "successful": cat_successful,
                "success_rate": f"{(cat_successful/len(cat_results)*100):.1f}%"
            }
        
        return {
            "overall": {
                "total_questions": total,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/total*100):.1f}%",
                "pattern_match_rate": f"{(pattern_matched/total*100):.1f}%"
            },
            "self_correction": {
                "total_retries": total_retries,
                "queries_with_retries": queries_with_retries,
                "retry_rate": f"{(queries_with_retries/total*100):.1f}%",
                "avg_retries_per_query": round(total_retries/total, 2)
            },
            "performance": {
                "avg_execution_time_ms": round(avg_execution_time, 2),
                "avg_total_time_ms": round(avg_total_time, 2),
                "total_evaluation_time_ms": round(sum(r["total_time_ms"] for r in self.results), 2)
            },
            "by_difficulty": by_difficulty,
            "by_category": by_category
        }
    
    def save_results(self, filepath: str):
        """Save detailed results to JSON file."""
        output = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "agent_config": {
                "model": self.agent.llm.model,
                "temperature": self.agent.temperature,
                "max_retries": self.agent.max_retries
            },
            "results": self.results,
            "metrics": self.get_metrics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✅ Results saved to: {filepath}")
    
    def print_summary(self):
        """Print evaluation summary."""
        metrics = self.get_metrics()
        
        print("\n" + "="*70)
        print("EVALUATION SUMMARY")
        print("="*70 + "\n")
        
        # Overall
        print("📊 OVERALL PERFORMANCE:")
        overall = metrics["overall"]
        print(f"  Total Questions: {overall['total_questions']}")
        print(f"  Successful: {overall['successful']}")
        print(f"  Failed: {overall['failed']}")
        print(f"  Success Rate: {overall['success_rate']}")
        print(f"  Pattern Match Rate: {overall['pattern_match_rate']}")
        print()
        
        # Self-correction
        print("🔄 SELF-CORRECTION:")
        correction = metrics["self_correction"]
        print(f"  Total Retries: {correction['total_retries']}")
        print(f"  Queries Needing Correction: {correction['queries_with_retries']}")
        print(f"  Retry Rate: {correction['retry_rate']}")
        print(f"  Avg Retries/Query: {correction['avg_retries_per_query']}")
        print()
        
        # Performance
        print("⚡ PERFORMANCE:")
        perf = metrics["performance"]
        print(f"  Avg Query Execution: {perf['avg_execution_time_ms']:.2f}ms")
        print(f"  Avg Total Time: {perf['avg_total_time_ms']:.2f}ms")
        print(f"  Total Evaluation Time: {perf['total_evaluation_time_ms']:.2f}ms")
        print()
        
        # By difficulty
        print("📈 BY DIFFICULTY:")
        for difficulty, stats in metrics["by_difficulty"].items():
            print(f"  {difficulty.capitalize()}: {stats['successful']}/{stats['total']} ({stats['success_rate']})")
        print()
        
        # Top categories
        print("📂 BY CATEGORY (Top 5):")
        sorted_cats = sorted(
            metrics["by_category"].items(),
            key=lambda x: float(x[1]["success_rate"].rstrip('%')),
            reverse=True
        )[:5]
        for category, stats in sorted_cats:
            print(f"  {category}: {stats['successful']}/{stats['total']} ({stats['success_rate']})")
        
        print()
