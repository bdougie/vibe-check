#!/usr/bin/env python3
"""
Metrics Extraction for Continue CLI Integration

Provides enhanced metrics collection and analysis for CN-based benchmark runs.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CNMetricsCollector:
    """Collects and analyzes metrics from Continue CLI benchmark runs."""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize metrics collector.
        
        Args:
            working_dir: Directory to analyze for changes
        """
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.initial_git_state = None
    
    def capture_initial_state(self):
        """Capture initial state before task execution."""
        self.initial_git_state = self.get_git_stats()
    
    def get_git_stats(self) -> Dict[str, Any]:
        """Get detailed git repository statistics.
        
        Returns:
            Dictionary with git metrics
        """
        try:
            stats = {
                "files_modified": 0,
                "lines_added": 0,
                "lines_removed": 0,
                "modified_files": [],
                "git_available": True
            }
            
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                stats["git_available"] = False
                return stats
            
            # Get modified files
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                modified_files = result.stdout.strip().split('\n')
                stats["modified_files"] = modified_files
                stats["files_modified"] = len(modified_files)
            
            # Get line statistics
            result = subprocess.run(
                ["git", "diff", "--numstat"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if line and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        try:
                            added = int(parts[0]) if parts[0] != '-' else 0
                            removed = int(parts[1]) if parts[1] != '-' else 0
                            stats["lines_added"] += added
                            stats["lines_removed"] += removed
                        except ValueError:
                            continue
            
            return stats
            
        except Exception as e:
            logger.warning(f"Could not get git stats: {e}")
            return {
                "files_modified": 0,
                "lines_added": 0,
                "lines_removed": 0,
                "modified_files": [],
                "git_available": False,
                "error": str(e)
            }
    
    def analyze_cn_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Analyze CN output for detailed metrics.
        
        Args:
            stdout: Standard output from CN
            stderr: Standard error from CN
            
        Returns:
            Dictionary of extracted metrics
        """
        combined_output = f"{stdout}\n{stderr}"
        
        metrics = {
            "tool_calls": 0,
            "files_read": 0,
            "files_written": 0,
            "bash_commands": 0,
            "errors_detected": 0,
            "success_indicators": 0,
            "output_length": len(combined_output),
            "lines_of_output": len(combined_output.split('\n')),
        }
        
        # Define patterns for different actions
        patterns = {
            "files_read": [
                r"Reading file:?\s+(.+)",
                r"Read file:?\s+(.+)",
                r"Opening file:?\s+(.+)",
                r"Loading file:?\s+(.+)"
            ],
            "files_written": [
                r"Writing to file:?\s+(.+)",
                r"Wrote file:?\s+(.+)",
                r"Modified file:?\s+(.+)",
                r"Saved file:?\s+(.+)",
                r"Updated file:?\s+(.+)"
            ],
            "bash_commands": [
                r"Running command:?\s+(.+)",
                r"Executing:?\s+(.+)",
                r"Command:?\s+(.+)"
            ],
            "errors_detected": [
                r"Error:?\s+(.+)",
                r"Failed:?\s+(.+)",
                r"Exception:?\s+(.+)",
                r"Warning:?\s+(.+)"
            ],
            "success_indicators": [
                r"Successfully (.+)",
                r"Completed (.+)",
                r"Fixed (.+)",
                r"Done (.+)",
                r"Task completed"
            ]
        }
        
        # Extract metrics using patterns
        for metric_name, pattern_list in patterns.items():
            count = 0
            extracted_items = []
            
            for pattern in pattern_list:
                matches = re.finditer(pattern, combined_output, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    count += 1
                    if len(match.groups()) > 0:
                        extracted_items.append(match.group(1).strip())
                    else:
                        extracted_items.append(match.group(0).strip())
            
            metrics[metric_name] = count
            if extracted_items:
                metrics[f"{metric_name}_details"] = extracted_items
        
        # Calculate total tool calls
        metrics["tool_calls"] = (
            metrics["files_read"] + 
            metrics["files_written"] + 
            metrics["bash_commands"]
        )
        
        # Determine success probability
        success_score = metrics["success_indicators"] * 2 - metrics["errors_detected"]
        metrics["success_score"] = max(0, success_score)
        metrics["likely_success"] = success_score > 0
        
        return metrics
    
    def analyze_task_completion(self, task_file: str, cn_output: str) -> Dict[str, Any]:
        """Analyze how well the task was completed based on requirements.
        
        Args:
            task_file: Path to the original task file
            cn_output: Output from CN execution
            
        Returns:
            Dictionary with completion analysis
        """
        try:
            with open(task_file, 'r') as f:
                task_content = f.read()
        except Exception as e:
            return {"error": f"Could not read task file: {e}"}
        
        # Extract requirements and success criteria
        requirements = self._extract_requirements(task_content)
        success_criteria = self._extract_success_criteria(task_content)
        
        analysis = {
            "total_requirements": len(requirements),
            "total_success_criteria": len(success_criteria),
            "requirements_met": 0,
            "criteria_met": 0,
            "requirements_analysis": [],
            "criteria_analysis": []
        }
        
        # Analyze requirements
        for req in requirements:
            met = self._check_requirement_met(req, cn_output)
            analysis["requirements_analysis"].append({
                "requirement": req,
                "met": met,
                "confidence": 0.5  # Basic heuristic
            })
            if met:
                analysis["requirements_met"] += 1
        
        # Analyze success criteria
        for criteria in success_criteria:
            met = self._check_criteria_met(criteria, cn_output)
            analysis["criteria_analysis"].append({
                "criteria": criteria,
                "met": met,
                "confidence": 0.5
            })
            if met:
                analysis["criteria_met"] += 1
        
        # Calculate completion percentage
        total_items = analysis["total_requirements"] + analysis["total_success_criteria"]
        completed_items = analysis["requirements_met"] + analysis["criteria_met"]
        
        analysis["completion_percentage"] = (
            (completed_items / total_items * 100) if total_items > 0 else 0
        )
        
        return analysis
    
    def _extract_requirements(self, task_content: str) -> List[str]:
        """Extract requirements from task markdown."""
        requirements = []
        lines = task_content.split('\n')
        in_requirements = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('## Requirements'):
                in_requirements = True
                continue
            elif line.startswith('##'):
                in_requirements = False
            elif in_requirements and line.startswith('- '):
                requirements.append(line[2:].strip())
        
        return requirements
    
    def _extract_success_criteria(self, task_content: str) -> List[str]:
        """Extract success criteria from task markdown."""
        criteria = []
        lines = task_content.split('\n')
        in_criteria = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('## Success Criteria'):
                in_criteria = True
                continue
            elif line.startswith('##'):
                in_criteria = False
            elif in_criteria and line.startswith('- [ ]'):
                criteria.append(line[5:].strip())
        
        return criteria
    
    def _check_requirement_met(self, requirement: str, cn_output: str) -> bool:
        """Check if a requirement appears to be met based on CN output."""
        # Simple heuristic - look for key terms from requirement in output
        req_lower = requirement.lower()
        output_lower = cn_output.lower()
        
        # Common success patterns
        success_patterns = [
            "fix", "fixed", "correct", "corrected",
            "modify", "modified", "update", "updated", 
            "change", "changed", "complete", "completed"
        ]
        
        # Check if requirement keywords appear with success patterns
        req_words = req_lower.split()
        key_words = [w for w in req_words if len(w) > 3 and w not in ['the', 'and', 'that', 'this']]
        
        for key_word in key_words[:3]:  # Check top 3 key words
            if key_word in output_lower:
                for pattern in success_patterns:
                    if pattern in output_lower:
                        return True
        
        return False
    
    def _check_criteria_met(self, criteria: str, cn_output: str) -> bool:
        """Check if success criteria appears to be met."""
        return self._check_requirement_met(criteria, cn_output)
    
    def generate_comprehensive_metrics(self, task_file: str, model_name: str,
                                     cn_output: str, cn_stderr: str, 
                                     execution_time: float, success: bool) -> Dict[str, Any]:
        """Generate comprehensive metrics for a CN benchmark run.
        
        Args:
            task_file: Path to task file
            model_name: Name of model used
            cn_output: Standard output from CN
            cn_stderr: Standard error from CN
            execution_time: Time taken to execute
            success: Whether the command succeeded
            
        Returns:
            Comprehensive metrics dictionary
        """
        # Get current git stats
        git_stats = self.get_git_stats()
        
        # Analyze CN output
        output_metrics = self.analyze_cn_output(cn_output, cn_stderr)
        
        # Analyze task completion
        completion_analysis = self.analyze_task_completion(task_file, cn_output)
        
        # Combine all metrics
        comprehensive_metrics = {
            "timestamp": datetime.now().isoformat(),
            "task_file": str(task_file),
            "model_name": model_name,
            "execution_time": execution_time,
            "command_success": success,
            
            # Git metrics
            "git": git_stats,
            
            # CN output analysis
            "output_analysis": output_metrics,
            
            # Task completion analysis
            "completion_analysis": completion_analysis,
            
            # High-level summary
            "summary": {
                "files_changed": git_stats.get("files_modified", 0),
                "total_tool_calls": output_metrics.get("tool_calls", 0),
                "completion_rate": completion_analysis.get("completion_percentage", 0),
                "likely_success": output_metrics.get("likely_success", False),
                "performance_score": self._calculate_performance_score(
                    execution_time, git_stats, output_metrics, completion_analysis
                )
            }
        }
        
        return comprehensive_metrics
    
    def _calculate_performance_score(self, execution_time: float, git_stats: Dict,
                                   output_metrics: Dict, completion_analysis: Dict) -> float:
        """Calculate a performance score (0-100) for the benchmark run."""
        score = 0.0
        
        # Completion rate (40% of score)
        completion_rate = completion_analysis.get("completion_percentage", 0)
        score += (completion_rate / 100) * 40
        
        # Efficiency - fewer tool calls is better (20% of score)
        tool_calls = output_metrics.get("tool_calls", 0)
        if tool_calls == 0:
            efficiency_score = 20
        else:
            efficiency_score = max(0, 20 - (tool_calls - 1) * 2)  # Penalty for many tool calls
        score += min(20, efficiency_score)
        
        # Speed - faster is better (20% of score)
        if execution_time <= 30:
            speed_score = 20
        elif execution_time <= 60:
            speed_score = 15
        elif execution_time <= 120:
            speed_score = 10
        else:
            speed_score = max(0, 10 - (execution_time - 120) / 60)
        score += speed_score
        
        # Quality - no errors is better (20% of score)
        errors = output_metrics.get("errors_detected", 0)
        success_indicators = output_metrics.get("success_indicators", 0)
        quality_score = max(0, 20 - errors * 5) + min(5, success_indicators * 2)
        score += min(20, quality_score)
        
        return round(score, 1)


def test_metrics_collector():
    """Test the metrics collector."""
    collector = CNMetricsCollector()
    
    # Test git stats
    git_stats = collector.get_git_stats()
    print("Git stats:", json.dumps(git_stats, indent=2))
    
    # Test output analysis
    sample_output = """
    Reading file: sample.py
    Found typo in line 12
    Writing to file: sample.py
    Successfully fixed typo
    Task completed
    """
    
    output_metrics = collector.analyze_cn_output(sample_output, "")
    print("Output metrics:", json.dumps(output_metrics, indent=2))


if __name__ == "__main__":
    test_metrics_collector()
