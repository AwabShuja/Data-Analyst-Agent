"""
Evaluation Dashboard - Visualize agent performance metrics.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.metrics import MetricsTracker


class EvaluationDashboard:
    """
    Text-based dashboard for viewing evaluation metrics.
    Shows trends, comparisons, and detailed breakdowns.
    """
    
    def __init__(self, tracker: MetricsTracker):
        """
        Initialize dashboard.
        
        Args:
            tracker: MetricsTracker instance
        """
        self.tracker = tracker
    
    def show_overview(self):
        """Show overview of all evaluation runs."""
        runs = self.tracker.get_all_runs()
        
        if not runs:
            print("\n❌ No evaluation runs found.\n")
            return
        
        print("\n" + "="*90)
        print("EVALUATION RUNS OVERVIEW")
        print("="*90 + "\n")
        
        print(f"{'ID':<6} {'Timestamp':<20} {'Model':<25} {'Success':<10} {'Exec Time':<12} {'Retries':<10}")
        print("-"*90)
        
        for run in runs:
            print(f"{run['run_id']:<6} "
                  f"{run['timestamp'][:19]:<20} "
                  f"{run['model'][:24]:<25} "
                  f"{run['success_rate']:.1f}%{'':<6} "
                  f"{run['avg_execution_time_ms']:.1f}ms{'':<7} "
                  f"{run['avg_retries_per_query']:.2f}")
        
        print("\n" + "="*90 + "\n")
    
    def show_statistics(self):
        """Show overall statistics across all runs."""
        stats = self.tracker.get_statistics()
        
        if not stats or stats.get('total_runs', 0) == 0:
            print("\n❌ No evaluation data available.\n")
            return
        
        print("\n" + "="*70)
        print("OVERALL STATISTICS")
        print("="*70 + "\n")
        
        print(f"📊 Total Evaluation Runs: {stats['total_runs']}")
        print(f"📈 Total Questions Evaluated: {stats['total_questions_evaluated']}")
        print()
        
        print(f"✅ Average Success Rate: {stats['avg_success_rate']:.1f}%")
        print(f"🏆 Best Success Rate: {stats['best_success_rate']:.1f}%")
        print(f"📉 Worst Success Rate: {stats['worst_success_rate']:.1f}%")
        print()
        
        print(f"⚡ Average Execution Time: {stats['avg_exec_time']:.2f}ms")
        print()
    
    def show_trend(self, metric: str = "success_rate", limit: int = 10):
        """
        Show trend for a specific metric.
        
        Args:
            metric: Metric to show trend for
            limit: Number of recent runs
        """
        trend_data = self.tracker.get_trend(metric, limit)
        
        if isinstance(trend_data, dict) and "error" in trend_data:
            print(f"\n❌ {trend_data['error']}\n")
            return
        
        if not trend_data:
            print(f"\n❌ No trend data available for {metric}\n")
            return
        
        print("\n" + "="*70)
        print(f"TREND: {metric.upper()}")
        print("="*70 + "\n")
        
        # Reverse to show oldest first
        trend_data.reverse()
        
        # Simple text-based chart
        values = [d['value'] for d in trend_data]
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        
        chart_width = 50
        
        for i, data in enumerate(trend_data, 1):
            timestamp = data['timestamp'][:16]  # Show date and time
            value = data['value']
            
            # Normalize to chart width
            if range_val > 0:
                bar_length = int(((value - min_val) / range_val) * chart_width)
            else:
                bar_length = chart_width
            
            bar = "█" * bar_length
            
            print(f"{i:2}. {timestamp} │ {bar} {value:.2f}")
        
        print(f"\nRange: {min_val:.2f} - {max_val:.2f}")
        print()
    
    def show_comparison(self, run_id1: int, run_id2: int):
        """
        Show comparison between two runs.
        
        Args:
            run_id1: First run ID
            run_id2: Second run ID
        """
        comparison = self.tracker.compare_runs(run_id1, run_id2)
        
        if "error" in comparison:
            print(f"\n❌ {comparison['error']}\n")
            return
        
        print("\n" + "="*70)
        print("RUN COMPARISON")
        print("="*70 + "\n")
        
        # Run info
        print(f"RUN 1: ID {comparison['run1']['run_id']}")
        print(f"  Timestamp: {comparison['run1']['timestamp']}")
        print(f"  Model: {comparison['run1']['model']}")
        print()
        
        print(f"RUN 2: ID {comparison['run2']['run_id']}")
        print(f"  Timestamp: {comparison['run2']['timestamp']}")
        print(f"  Model: {comparison['run2']['model']}")
        print()
        
        print("="*70)
        print("METRIC CHANGES")
        print("="*70 + "\n")
        
        # Metrics comparison
        changes = comparison['changes']
        
        for metric_name, metric_data in changes.items():
            change_pct = metric_data['change_pct']
            
            # Format metric name
            display_name = metric_name.replace('_', ' ').title()
            
            # Direction indicator
            if change_pct > 0:
                indicator = "📈" if "time" not in metric_name.lower() and "retries" not in metric_name.lower() else "📉"
                direction = "increase"
            elif change_pct < 0:
                indicator = "📉" if "time" not in metric_name.lower() and "retries" not in metric_name.lower() else "📈"
                direction = "decrease"
            else:
                indicator = "➡️"
                direction = "no change"
            
            print(f"{display_name}:")
            print(f"  Run 1: {metric_data['run1']:.2f}")
            print(f"  Run 2: {metric_data['run2']:.2f}")
            print(f"  Change: {indicator} {abs(change_pct):.1f}% {direction}")
            print()
    
    def show_run_details(self, run_id: int):
        """
        Show detailed information about a specific run.
        
        Args:
            run_id: Run ID to show details for
        """
        run = self.tracker.get_run(run_id)
        
        if not run:
            print(f"\n❌ Run ID {run_id} not found.\n")
            return
        
        print("\n" + "="*70)
        print(f"RUN DETAILS - ID {run_id}")
        print("="*70 + "\n")
        
        print(f"Timestamp: {run['timestamp']}")
        print(f"Model: {run['model']}")
        print(f"Temperature: {run['temperature']}")
        print(f"Max Retries: {run['max_retries']}")
        if run['notes']:
            print(f"Notes: {run['notes']}")
        print()
        
        print("PERFORMANCE:")
        print(f"  Total Questions: {run['total_questions']}")
        print(f"  Successful: {run['successful']}")
        print(f"  Failed: {run['failed']}")
        print(f"  Success Rate: {run['success_rate']:.1f}%")
        print(f"  Pattern Match Rate: {run['pattern_match_rate']:.1f}%")
        print()
        
        print("SELF-CORRECTION:")
        print(f"  Total Retries: {run['total_retries']}")
        print(f"  Avg Retries/Query: {run['avg_retries_per_query']:.2f}")
        print()
        
        print("TIMING:")
        print(f"  Avg Execution Time: {run['avg_execution_time_ms']:.2f}ms")
        print(f"  Avg Total Time: {run['avg_total_time_ms']:.2f}ms")
        print(f"  Total Evaluation Time: {run['total_evaluation_time_ms']:.2f}ms")
        print()
    
    def interactive_menu(self):
        """Show interactive menu for dashboard."""
        while True:
            print("\n" + "="*70)
            print("EVALUATION DASHBOARD")
            print("="*70)
            print("\n1. Show All Runs Overview")
            print("2. Show Overall Statistics")
            print("3. Show Trend (Success Rate)")
            print("4. Show Trend (Execution Time)")
            print("5. Show Trend (Retry Rate)")
            print("6. Compare Two Runs")
            print("7. Show Run Details")
            print("0. Exit")
            
            choice = input("\nYour choice (0-7): ").strip()
            
            if choice == "1":
                self.show_overview()
            elif choice == "2":
                self.show_statistics()
            elif choice == "3":
                self.show_trend("success_rate", limit=10)
            elif choice == "4":
                self.show_trend("avg_execution_time_ms", limit=10)
            elif choice == "5":
                self.show_trend("avg_retries_per_query", limit=10)
            elif choice == "6":
                try:
                    run_id1 = int(input("Enter first run ID: ").strip())
                    run_id2 = int(input("Enter second run ID: ").strip())
                    self.show_comparison(run_id1, run_id2)
                except ValueError:
                    print("\n❌ Invalid run ID format.\n")
            elif choice == "7":
                try:
                    run_id = int(input("Enter run ID: ").strip())
                    self.show_run_details(run_id)
                except ValueError:
                    print("\n❌ Invalid run ID format.\n")
            elif choice == "0":
                print("\n👋 Goodbye!\n")
                break
            else:
                print("\n❌ Invalid choice.\n")
            
            if choice != "0":
                input("\nPress Enter to continue...")
