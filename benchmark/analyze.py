#!/usr/bin/env python3
import csv
import io
import json
from pathlib import Path
import statistics
import sys
from typing import List, Dict, Any, Optional

# Try to import pandas and visualization libraries
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas/matplotlib/seaborn not available. Install for enhanced analysis:")
    print("   uv pip install pandas matplotlib seaborn")
    print("   Falling back to basic analysis...\n")


def load_results() -> List[Dict[str, Any]]:
    """Load all benchmark results from the results directory"""
    results = []
    results_path = Path("benchmark/results")

    if not results_path.exists():
        print("No results directory found. Run some benchmarks first!")
        return results

    # Pre-load all files to avoid try-except in loop
    json_files = list(results_path.glob("*.json"))

    for result_file in json_files:
        data = json.loads(result_file.read_text())
        data["filename"] = result_file.name
        results.append(data)

    return results


def print_overall_stats(results):
    """Print overall benchmark statistics"""
    print("\n📊 Overall Statistics")
    print("-" * 40)
    print(f"Total tasks attempted: {len(results)}")

    completed = [r for r in results if r.get("task_completed", False)]
    completion_rate = len(completed) / len(results) * 100 if results else 0
    print(f"Completion rate: {completion_rate:.1f}% ({len(completed)}/{len(results)})")

    if completed:
        avg_time = statistics.mean([r.get("completion_time", 0) for r in completed])
        print(f"Average completion time: {avg_time / 60:.1f} minutes")


def print_model_performance(results):
    """Print performance statistics by model"""
    models = {}
    for result in results:
        model = result.get("model", "Unknown")
        if model not in models:
            models[model] = []
        models[model].append(result)

    print("\n🤖 Performance by Model")
    print("-" * 40)
    print(f"{'Model':<25} {'Tasks':<8} {'Success':<10} {'Avg Time':<12} {'Prompts'}")
    print("-" * 70)

    for model, model_results in sorted(models.items()):
        completed_tasks = [r for r in model_results if r.get("task_completed", False)]
        success_rate = (
            len(completed_tasks) / len(model_results) * 100 if model_results else 0
        )

        avg_time = 0
        avg_prompts = 0
        if completed_tasks:
            avg_time = statistics.mean(
                [r.get("completion_time", 0) for r in completed_tasks]
            )
            avg_prompts = statistics.mean(
                [r.get("prompts_sent", 0) for r in completed_tasks]
            )

        print(
            f"{model:<25} {len(model_results):<8} {success_rate:<9.1f}% "
            f"{avg_time / 60:<11.1f}m {avg_prompts:<.1f}"
        )


def print_task_performance(results):
    """Print performance statistics by task"""
    tasks = {}
    for result in results:
        task = result.get("task", "Unknown")
        if task not in tasks:
            tasks[task] = []
        tasks[task].append(result)

    print("\n📝 Performance by Task")
    print("-" * 40)
    print(f"{'Task':<30} {'Attempts':<10} {'Success Rate':<15} {'Avg Prompts'}")
    print("-" * 70)

    for task, task_results in sorted(tasks.items()):
        completed_tasks = [r for r in task_results if r.get("task_completed", False)]
        success_rate = (
            len(completed_tasks) / len(task_results) * 100 if task_results else 0
        )

        avg_prompts = 0
        if completed_tasks:
            avg_prompts = statistics.mean(
                [r.get("prompts_sent", 0) for r in completed_tasks]
            )

        print(
            f"{task:<30} {len(task_results):<10} {success_rate:<14.1f}% {avg_prompts:<.1f}"
        )


def analyze_with_pandas(results: List[Dict[str, Any]]):
    """Enhanced analysis using pandas DataFrames"""
    df = pd.DataFrame(results)
    
    print("\n📊 Enhanced Pandas Analysis")
    print("=" * 70)
    
    # Overall statistics
    print("\n📈 Dataset Overview:")
    print(f"Total benchmark runs: {len(df)}")
    print(f"Unique models tested: {df['model'].nunique()}")
    print(f"Unique tasks tested: {df['task'].nunique()}")
    print(f"Date range: {df['timestamp'].min()[:10] if 'timestamp' in df else 'N/A'} to {df['timestamp'].max()[:10] if 'timestamp' in df else 'N/A'}")
    
    # Success rate analysis
    print("\n✅ Success Rate Analysis:")
    success_df = df.groupby('model').agg({
        'task_completed': ['count', 'sum', 'mean']
    }).round(3)
    success_df.columns = ['Total Tasks', 'Completed', 'Success Rate']
    success_df['Success Rate'] = (success_df['Success Rate'] * 100).round(1)
    print(success_df.to_string())
    
    # Performance metrics by model
    print("\n⚡ Performance Metrics by Model:")
    completed_df = df[df['task_completed'] == True]
    if not completed_df.empty:
        perf_df = completed_df.groupby('model').agg({
            'completion_time': 'mean',
            'prompts_sent': 'mean',
            'human_interventions': 'mean',
            'lines_added': 'sum',
            'lines_removed': 'sum'
        }).round(1)
        perf_df['completion_time'] = (perf_df['completion_time'] / 60).round(1)
        perf_df.columns = ['Avg Time (min)', 'Avg Prompts', 'Avg Interventions', 'Total Lines Added', 'Total Lines Removed']
        print(perf_df.to_string())
    
    # Task difficulty analysis
    print("\n🎯 Task Difficulty Analysis:")
    task_stats = df.groupby('task').agg({
        'task_completed': ['count', 'mean'],
        'prompts_sent': 'mean',
        'completion_time': 'mean'
    }).round(2)
    task_stats.columns = ['Attempts', 'Success Rate', 'Avg Prompts', 'Avg Time (sec)']
    task_stats['Success Rate'] = (task_stats['Success Rate'] * 100).round(1)
    task_stats = task_stats.sort_values('Success Rate', ascending=False)
    print(task_stats.head(10).to_string())
    
    # Model comparison matrix
    if df['model'].nunique() > 1 and df['task'].nunique() > 1:
        print("\n🔄 Model vs Task Success Matrix:")
        pivot_table = pd.pivot_table(
            df, 
            values='task_completed',
            index='task',
            columns='model',
            aggfunc='mean',
            fill_value=0
        ) * 100
        print(pivot_table.round(1).to_string())
    
    # Time series analysis if timestamps available
    if 'timestamp' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        print("\n📅 Daily Activity:")
        daily_stats = df.groupby('date').agg({
            'task_completed': ['count', 'mean']
        })
        daily_stats.columns = ['Tasks Run', 'Success Rate']
        daily_stats['Success Rate'] = (daily_stats['Success Rate'] * 100).round(1)
        print(daily_stats.tail(7).to_string())


def visualize_results():
    """Generate visualization charts for benchmark results"""
    if not PANDAS_AVAILABLE:
        print("Visualization requires pandas, matplotlib, and seaborn. Please install them first.")
        return
    
    results = load_results()
    if not results:
        print("No results to visualize")
        return
    
    df = pd.DataFrame(results)
    
    # Set up the plot style
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('AI Coding Agent Benchmark Results', fontsize=16, fontweight='bold')
    
    # 1. Success rate by model
    ax1 = axes[0, 0]
    model_success = df.groupby('model')['task_completed'].mean() * 100
    model_success.plot(kind='bar', ax=ax1, color='skyblue', edgecolor='black')
    ax1.set_title('Success Rate by Model')
    ax1.set_xlabel('Model')
    ax1.set_ylabel('Success Rate (%)')
    ax1.set_ylim(0, 105)
    for i, v in enumerate(model_success):
        ax1.text(i, v + 1, f'{v:.1f}%', ha='center')
    
    # 2. Average completion time by model
    ax2 = axes[0, 1]
    completed_df = df[df['task_completed'] == True]
    if not completed_df.empty:
        avg_time = completed_df.groupby('model')['completion_time'].mean() / 60
        avg_time.plot(kind='bar', ax=ax2, color='lightcoral', edgecolor='black')
        ax2.set_title('Average Completion Time by Model')
        ax2.set_xlabel('Model')
        ax2.set_ylabel('Time (minutes)')
        for i, v in enumerate(avg_time):
            ax2.text(i, v + 0.5, f'{v:.1f}', ha='center')
    
    # 3. Task difficulty distribution
    ax3 = axes[1, 0]
    task_attempts = df['task'].value_counts().head(10)
    task_attempts.plot(kind='barh', ax=ax3, color='lightgreen', edgecolor='black')
    ax3.set_title('Top 10 Most Attempted Tasks')
    ax3.set_xlabel('Number of Attempts')
    ax3.set_ylabel('Task')
    
    # 4. Human interventions scatter plot
    ax4 = axes[1, 1]
    if 'prompts_sent' in df.columns and 'human_interventions' in df.columns:
        colors = ['green' if x else 'red' for x in df['task_completed']]
        ax4.scatter(df['prompts_sent'], df['human_interventions'], 
                   c=colors, alpha=0.6, edgecolors='black')
        ax4.set_title('Prompts vs Human Interventions')
        ax4.set_xlabel('Prompts Sent')
        ax4.set_ylabel('Human Interventions')
        ax4.legend(['Completed', 'Failed'], loc='upper right')
    
    plt.tight_layout()
    
    # Save the figure
    output_path = Path('benchmark/results_visualization.png')
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    print(f"\n📊 Visualization saved to {output_path}")
    
    # Show the plot if in interactive environment
    try:
        plt.show()
    except:
        print("Cannot display plot in this environment. Check the saved file.")


def print_intervention_analysis(results):
    """Print human intervention analysis"""
    print("\n👤 Human Intervention Analysis")
    print("-" * 40)

    all_interventions = [r.get("human_interventions", 0) for r in results]
    if all_interventions:
        print(
            f"Average interventions per task: {statistics.mean(all_interventions):.1f}"
        )
        print(f"Max interventions: {max(all_interventions)}")
        print(f"Min interventions: {min(all_interventions)}")

        no_intervention = len([i for i in all_interventions if i == 0])
        intervention_rate = no_intervention / len(results) * 100
        print(
            f"Tasks completed without intervention: {no_intervention} ({intervention_rate:.1f}%)"
        )


def print_code_change_stats(results):
    """Print code change statistics"""
    print("\n📄 Code Change Statistics")
    print("-" * 40)

    completed = [r for r in results if r.get("task_completed", False)]
    code_changes = [
        (r.get("files_modified", 0), r.get("lines_added", 0), r.get("lines_removed", 0))
        for r in completed
    ]

    if code_changes:
        avg_files = statistics.mean([c[0] for c in code_changes])
        avg_added = statistics.mean([c[1] for c in code_changes])
        avg_removed = statistics.mean([c[2] for c in code_changes])

        print(f"Average files modified: {avg_files:.1f}")
        print(f"Average lines added: {avg_added:.1f}")
        print(f"Average lines removed: {avg_removed:.1f}")


def analyze_results():
    """Analyze benchmark results and display statistics"""
    results = load_results()

    if not results:
        print("No benchmark results found. Run some benchmarks first!")
        return

    print("\n" + "=" * 70)
    print(" " * 20 + "BENCHMARK RESULTS ANALYSIS")
    print("=" * 70)

    # Use pandas for enhanced analysis if available
    if PANDAS_AVAILABLE:
        analyze_with_pandas(results)
    else:
        # Fallback to basic analysis
        print_overall_stats(results)
        print_model_performance(results)
        print_task_performance(results)
        print_intervention_analysis(results)
        print_code_change_stats(results)

    print("\n" + "=" * 70 + "\n")


def export_to_csv():
    """Export results to CSV for further analysis"""
    results = load_results()
    if not results:
        print("No results to export")
        return

    csv_file = Path("benchmark/results_summary.csv")

    # Use pandas if available for better export
    if PANDAS_AVAILABLE:
        df = pd.DataFrame(results)
        df.to_csv(csv_file, index=False)
        print(f"✅ Results exported to {csv_file} using pandas")
        print(f"   Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    else:
        fieldnames = [
            "filename",
            "model",
            "task",
            "task_completed",
            "completion_time",
            "prompts_sent",
            "chars_sent",
            "chars_received",
            "human_interventions",
            "files_modified",
            "lines_added",
            "lines_removed",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

        csv_file.write_text(output.getvalue())
        print(f"Results exported to {csv_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--export":
            export_to_csv()
        elif sys.argv[1] == "--visualize" and PANDAS_AVAILABLE:
            visualize_results()
        elif sys.argv[1] == "--help":
            print("Usage: python benchmark/analyze.py [OPTIONS]")
            print("\nOptions:")
            print("  --export     Export results to CSV")
            print("  --visualize  Generate visualization charts (requires pandas/matplotlib)")
            print("  --help       Show this help message")
        else:
            analyze_results()
    else:
        analyze_results()
        print("\nTip: Run with --export flag to export results to CSV")
        if PANDAS_AVAILABLE:
            print("     Run with --visualize flag to generate charts")
