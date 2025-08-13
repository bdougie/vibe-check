#!/usr/bin/env python3
import json
import statistics
from pathlib import Path

def load_results():
    """Load all benchmark results from the results directory"""
    results = []
    results_path = Path("benchmark/results")

    if not results_path.exists():
        print("No results directory found. Run some benchmarks first!")
        return results

    for result_file in results_path.glob("*.json"):
        try:
            data = json.loads(result_file.read_text())
            data['filename'] = result_file.name
            results.append(data)
        except Exception as e:
            print(f"Error loading {result_file}: {e}")

    return results

def print_overall_stats(results):
    """Print overall benchmark statistics"""
    print(f"\n📊 Overall Statistics")
    print("-" * 40)
    print(f"Total tasks attempted: {len(results)}")

    completed = [r for r in results if r.get('task_completed', False)]
    completion_rate = len(completed) / len(results) * 100 if results else 0
    print(f"Completion rate: {completion_rate:.1f}% ({len(completed)}/{len(results)})")

    if completed:
        avg_time = statistics.mean([r.get('completion_time', 0) for r in completed])
        print(f"Average completion time: {avg_time/60:.1f} minutes")


def print_model_performance(results):
    """Print performance statistics by model"""
    models = {}
    for result in results:
        model = result.get('model', 'Unknown')
        if model not in models:
            models[model] = []
        models[model].append(result)

    print(f"\n🤖 Performance by Model")
    print("-" * 40)
    print(f"{'Model':<25} {'Tasks':<8} {'Success':<10} {'Avg Time':<12} {'Prompts'}")
    print("-" * 70)

    for model, model_results in sorted(models.items()):
        completed_tasks = [r for r in model_results if r.get('task_completed', False)]
        success_rate = len(completed_tasks) / len(model_results) * 100 if model_results else 0

        avg_time = 0
        avg_prompts = 0
        if completed_tasks:
            avg_time = statistics.mean([r.get('completion_time', 0) for r in completed_tasks])
            avg_prompts = statistics.mean([r.get('prompts_sent', 0) for r in completed_tasks])

        print(f"{model:<25} {len(model_results):<8} {success_rate:<9.1f}% "
              f"{avg_time/60:<11.1f}m {avg_prompts:<.1f}")


def print_task_performance(results):
    """Print performance statistics by task"""
    tasks = {}
    for result in results:
        task = result.get('task', 'Unknown')
        if task not in tasks:
            tasks[task] = []
        tasks[task].append(result)

    print(f"\n📝 Performance by Task")
    print("-" * 40)
    print(f"{'Task':<30} {'Attempts':<10} {'Success Rate':<15} {'Avg Prompts'}")
    print("-" * 70)

    for task, task_results in sorted(tasks.items()):
        completed_tasks = [r for r in task_results if r.get('task_completed', False)]
        success_rate = len(completed_tasks) / len(task_results) * 100 if task_results else 0

        avg_prompts = 0
        if completed_tasks:
            avg_prompts = statistics.mean([r.get('prompts_sent', 0) for r in completed_tasks])

        print(f"{task:<30} {len(task_results):<10} {success_rate:<14.1f}% {avg_prompts:<.1f}")


def print_intervention_analysis(results):
    """Print human intervention analysis"""
    print(f"\n👤 Human Intervention Analysis")
    print("-" * 40)

    all_interventions = [r.get('human_interventions', 0) for r in results]
    if all_interventions:
        print(f"Average interventions per task: {statistics.mean(all_interventions):.1f}")
        print(f"Max interventions: {max(all_interventions)}")
        print(f"Min interventions: {min(all_interventions)}")

        no_intervention = len([i for i in all_interventions if i == 0])
        intervention_rate = no_intervention/len(results)*100
        print(f"Tasks completed without intervention: {no_intervention} ({intervention_rate:.1f}%)")


def print_code_change_stats(results):
    """Print code change statistics"""
    print(f"\n📄 Code Change Statistics")
    print("-" * 40)

    completed = [r for r in results if r.get('task_completed', False)]
    code_changes = [(r.get('files_modified', 0),
                    r.get('lines_added', 0),
                    r.get('lines_removed', 0)) for r in completed]

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

    print("\n" + "="*70)
    print(" " * 20 + "BENCHMARK RESULTS ANALYSIS")
    print("="*70)

    print_overall_stats(results)
    print_model_performance(results)
    print_task_performance(results)
    print_intervention_analysis(results)
    print_code_change_stats(results)

    print("\n" + "="*70 + "\n")

def export_to_csv():
    """Export results to CSV for further analysis"""
    import csv
    import io

    results = load_results()
    if not results:
        print("No results to export")
        return

    csv_file = Path("benchmark/results_summary.csv")

    fieldnames = ['filename', 'model', 'task', 'task_completed', 'completion_time',
                  'prompts_sent', 'chars_sent', 'chars_received', 'human_interventions',
                  'files_modified', 'lines_added', 'lines_removed']

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(results)

    csv_file.write_text(output.getvalue())
    print(f"Results exported to {csv_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--export':
        export_to_csv()
    else:
        analyze_results()
        print("Tip: Run with --export flag to export results to CSV")