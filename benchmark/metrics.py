import json
import time
from datetime import datetime
from pathlib import Path


class BenchmarkMetrics:
    def __init__(self, model_name, task_name):
        self.model_name = model_name
        self.task_name = task_name
        self.start_time = None
        self.metrics = {
            'model': model_name,
            'task': task_name,
            'prompts_sent': 0,
            'chars_sent': 0,
            'chars_received': 0,
            'human_interventions': 0,
            'task_completed': False,
            'completion_time': 0,
            'files_modified': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'session_log': []
        }

    def start_task(self):
        self.start_time = time.time()
        self.log_event('task_started')

    def log_prompt(self, prompt_text, response_text):
        self.metrics['prompts_sent'] += 1
        self.metrics['chars_sent'] += len(prompt_text)
        self.metrics['chars_received'] += len(response_text)
        self.log_event('prompt_sent', {
            'prompt_length': len(prompt_text),
            'response_length': len(response_text)
        })

    def log_human_intervention(self, intervention_type):
        self.metrics['human_interventions'] += 1
        self.log_event('human_intervention', {'type': intervention_type})

    def complete_task(self, success=True):
        if self.start_time:
            self.metrics['completion_time'] = time.time() - self.start_time
        self.metrics['task_completed'] = success
        self.log_event('task_completed', {'success': success})

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = Path("benchmark/results")
        results_dir.mkdir(parents=True, exist_ok=True)

        filename = results_dir / f"{self.model_name}_{self.task_name}_{timestamp}.json"

        with filename.open('w') as f:
            json.dump(self.metrics, f, indent=2)

        return filename

    def log_event(self, event_type, data=None):
        event = {
            'timestamp': time.time(),
            'event': event_type,
            'data': data or {}
        }
        self.metrics['session_log'].append(event)

    def update_git_stats(self, files_modified, lines_added, lines_removed):
        self.metrics['files_modified'] = files_modified
        self.metrics['lines_added'] = lines_added
        self.metrics['lines_removed'] = lines_removed
        self.log_event('git_stats_updated', {
            'files': files_modified,
            'added': lines_added,
            'removed': lines_removed
        })