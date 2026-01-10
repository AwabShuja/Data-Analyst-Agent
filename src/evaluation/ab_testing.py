"""
A/B Testing - Compare different agent configurations.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.evaluator import AgentEvaluator
from evaluation.metrics import MetricsTracker
from agent.sql_agent import SQLAgent


class ABComparator:
    """
    A/B testing framework for comparing agent configurations.
    
    Use cases:
    - Compare different models (Llama 3.1 70B vs Mixtral 8x7B)
    - Compare different temperatures (0.0 vs 0.1 vs 0.5)
    - Compare with/without self-correction
    - Baseline vs enhanced agent
    """
    
    def __init__(self, db_path: str = "data/processed/orders.db"):
        """
        Initialize A/B comparator.
        
        Args:
            db_path: Path to database
        """
        self.db_path = db_path
        self.tracker = MetricsTracker()
    
    def run_test(
        self,
        config_a: Dict[str, Any],
        config_b: Dict[str, Any],
        label_a: str = "Configuration A",
        label_b: str = "Configuration B",
        difficulty: Optional[str] = None,
        max_questions: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run A/B test comparing two configurations.
        
        Args:
            config_a: First agent configuration
            config_b: Second agent configuration
            label_a: Label for first configuration
            label_b: Label for second configuration
            difficulty: Filter questions by difficulty
            max_questions: Limit number of questions
            
        Returns:
            Comparison results
        """
        print("\n" + "="*70)
        print("A/B TEST")
        print("="*70 + "\n")
        
        print(f"Configuration A: {label_a}")
        print(f"  Model: {config_a.get('model', 'default')}")
        print(f"  Temperature: {config_a.get('temperature', 0.1)}")
        print(f"  Max Retries: {config_a.get('max_retries', 2)}")
        print()
        
        print(f"Configuration B: {label_b}")
        print(f"  Model: {config_b.get('model', 'default')}")
        print(f"  Temperature: {config_b.get('temperature', 0.1)}")
        print(f"  Max Retries: {config_b.get('max_retries', 2)}")
        print()
        
        # Run Configuration A
        print("="*70)
        print(f"TESTING: {label_a}")
        print("="*70)
        
        agent_a = SQLAgent(
            db_path=self.db_path,
            model=config_a.get('model', 'llama-3.1-8b-instant'),
            temperature=config_a.get('temperature', 0.1),
            max_retries=config_a.get('max_retries', 2)
        )
        
        evaluator_a = AgentEvaluator(agent_a)
        results_a = evaluator_a.evaluate_all(difficulty, max_questions)
        metrics_a = evaluator_a.get_metrics()
        
        # Save results
        run_id_a = self.tracker.save_run(
            results_a,
            metrics_a,
            config_a,
            notes=f"A/B Test - {label_a}"
        )
        
        print(f"\n✅ Configuration A completed. Run ID: {run_id_a}\n")
        
        # Run Configuration B
        print("="*70)
        print(f"TESTING: {label_b}")
        print("="*70)
        
        agent_b = SQLAgent(
            db_path=self.db_path,
            model=config_b.get('model', 'llama-3.1-8b-instant'),
            temperature=config_b.get('temperature', 0.1),
            max_retries=config_b.get('max_retries', 2)
        )
        
        evaluator_b = AgentEvaluator(agent_b)
        results_b = evaluator_b.evaluate_all(difficulty, max_questions)
        metrics_b = evaluator_b.get_metrics()
        
        # Save results
        run_id_b = self.tracker.save_run(
            results_b,
            metrics_b,
            config_b,
            notes=f"A/B Test - {label_b}"
        )
        
        print(f"\n✅ Configuration B completed. Run ID: {run_id_b}\n")
        
        # Compare results
        comparison = self._compare_metrics(metrics_a, metrics_b, label_a, label_b)
        comparison["run_id_a"] = run_id_a
        comparison["run_id_b"] = run_id_b
        
        return comparison
    
    def _compare_metrics(
        self,
        metrics_a: Dict[str, Any],
        metrics_b: Dict[str, Any],
        label_a: str,
        label_b: str
    ) -> Dict[str, Any]:
        """Compare two sets of metrics."""
        
        def extract_value(metric_str: str) -> float:
            """Extract numeric value from percentage string."""
            if isinstance(metric_str, str) and '%' in metric_str:
                return float(metric_str.rstrip('%'))
            return float(metric_str)
        
        def calculate_improvement(val_a: float, val_b: float, lower_is_better: bool = False) -> float:
            """Calculate improvement percentage."""
            if val_a == 0:
                return 0.0
            improvement = ((val_b - val_a) / val_a) * 100
            if lower_is_better:
                improvement = -improvement
            return improvement
        
        # Extract key metrics
        success_a = extract_value(metrics_a["overall"]["success_rate"])
        success_b = extract_value(metrics_b["overall"]["success_rate"])
        
        pattern_a = extract_value(metrics_a["overall"]["pattern_match_rate"])
        pattern_b = extract_value(metrics_b["overall"]["pattern_match_rate"])
        
        exec_time_a = metrics_a["performance"]["avg_execution_time_ms"]
        exec_time_b = metrics_b["performance"]["avg_execution_time_ms"]
        
        retries_a = metrics_a["self_correction"]["avg_retries_per_query"]
        retries_b = metrics_b["self_correction"]["avg_retries_per_query"]
        
        return {
            "config_a": label_a,
            "config_b": label_b,
            "metrics": {
                "success_rate": {
                    "a": success_a,
                    "b": success_b,
                    "improvement": round(calculate_improvement(success_a, success_b), 2),
                    "winner": label_b if success_b > success_a else label_a
                },
                "pattern_match_rate": {
                    "a": pattern_a,
                    "b": pattern_b,
                    "improvement": round(calculate_improvement(pattern_a, pattern_b), 2),
                    "winner": label_b if pattern_b > pattern_a else label_a
                },
                "avg_execution_time_ms": {
                    "a": exec_time_a,
                    "b": exec_time_b,
                    "improvement": round(calculate_improvement(exec_time_a, exec_time_b, lower_is_better=True), 2),
                    "winner": label_b if exec_time_b < exec_time_a else label_a
                },
                "avg_retries_per_query": {
                    "a": retries_a,
                    "b": retries_b,
                    "improvement": round(calculate_improvement(retries_a, retries_b, lower_is_better=True), 2),
                    "winner": label_b if retries_b < retries_a else label_a
                }
            }
        }
    
    def print_comparison(self, comparison: Dict[str, Any]):
        """Print A/B comparison results."""
        print("\n" + "="*70)
        print("A/B TEST RESULTS")
        print("="*70 + "\n")
        
        print(f"Configuration A: {comparison['config_a']}")
        print(f"Configuration B: {comparison['config_b']}")
        print()
        
        metrics = comparison["metrics"]
        
        print("="*70)
        print("METRIC COMPARISON")
        print("="*70 + "\n")
        
        # Success Rate
        sr = metrics["success_rate"]
        print("✅ SUCCESS RATE:")
        print(f"  {comparison['config_a']}: {sr['a']:.1f}%")
        print(f"  {comparison['config_b']}: {sr['b']:.1f}%")
        improvement_symbol = "📈" if sr['improvement'] > 0 else "📉" if sr['improvement'] < 0 else "➡️"
        print(f"  {improvement_symbol} Improvement: {abs(sr['improvement']):.1f}%")
        print(f"  🏆 Winner: {sr['winner']}")
        print()
        
        # Pattern Match Rate
        pm = metrics["pattern_match_rate"]
        print("🎯 PATTERN MATCH RATE:")
        print(f"  {comparison['config_a']}: {pm['a']:.1f}%")
        print(f"  {comparison['config_b']}: {pm['b']:.1f}%")
        improvement_symbol = "📈" if pm['improvement'] > 0 else "📉" if pm['improvement'] < 0 else "➡️"
        print(f"  {improvement_symbol} Improvement: {abs(pm['improvement']):.1f}%")
        print(f"  🏆 Winner: {pm['winner']}")
        print()
        
        # Execution Time
        et = metrics["avg_execution_time_ms"]
        print("⚡ AVG EXECUTION TIME:")
        print(f"  {comparison['config_a']}: {et['a']:.2f}ms")
        print(f"  {comparison['config_b']}: {et['b']:.2f}ms")
        improvement_symbol = "📈" if et['improvement'] > 0 else "📉" if et['improvement'] < 0 else "➡️"
        print(f"  {improvement_symbol} Improvement: {abs(et['improvement']):.1f}%")
        print(f"  🏆 Winner: {et['winner']}")
        print()
        
        # Retries
        rt = metrics["avg_retries_per_query"]
        print("🔄 AVG RETRIES PER QUERY:")
        print(f"  {comparison['config_a']}: {rt['a']:.2f}")
        print(f"  {comparison['config_b']}: {rt['b']:.2f}")
        improvement_symbol = "📈" if rt['improvement'] > 0 else "📉" if rt['improvement'] < 0 else "➡️"
        print(f"  {improvement_symbol} Improvement: {abs(rt['improvement']):.1f}%")
        print(f"  🏆 Winner: {rt['winner']}")
        print()
        
        # Overall winner (most wins)
        winners = [
            sr['winner'],
            pm['winner'],
            et['winner'],
            rt['winner']
        ]
        
        a_wins = winners.count(comparison['config_a'])
        b_wins = winners.count(comparison['config_b'])
        
        print("="*70)
        print("OVERALL WINNER")
        print("="*70 + "\n")
        
        if a_wins > b_wins:
            print(f"🏆 {comparison['config_a']} wins {a_wins}/4 metrics")
        elif b_wins > a_wins:
            print(f"🏆 {comparison['config_b']} wins {b_wins}/4 metrics")
        else:
            print(f"🤝 Tie: both win {a_wins}/4 metrics")
        
        print()
