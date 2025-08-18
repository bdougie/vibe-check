#!/usr/bin/env python3
"""
Debug script for Continue CLI integration
"""

import subprocess
import tempfile
import yaml
from pathlib import Path

def test_cn_with_model(model_name):
    """Test CN with a specific model."""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print('='*60)
    
    # Create a simple config matching Continue's expected format
    # Check if model supports tools natively
    supports_tools = "gpt-oss" in model_name.lower()
    
    model_config = {
        "name": model_name,
        "model": model_name,
        "provider": "ollama",
        "roles": ["chat"],
        "systemMessage": "You are a helpful coding assistant that can use tools to complete tasks."
    }
    
    # Only add capabilities for models that support tools
    if supports_tools:
        model_config["capabilities"] = ["tool_use"]
    
    config = {
        "name": "test-assistant",
        "version": "0.0.1",
        "models": [model_config]
    }
    
    # Write config to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    print(f"Config file: {config_path}")
    print("Config content:")
    print(yaml.dump(config, default_flow_style=False))
    
    # Simple test prompt
    prompt = "Say hello and tell me what model you are"
    
    # Build command
    cmd = [
        "cn",
        "-p", prompt,
        "--config", config_path
    ]
    
    print(f"\nCommand: {' '.join(cmd)}")
    
    # Execute
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"\nReturn code: {result.returncode}")
        
        if result.stdout:
            print(f"\nStdout:\n{result.stdout[:500]}")
        
        if result.stderr:
            print(f"\nStderr:\n{result.stderr[:500]}")
            
        # Cleanup
        Path(config_path).unlink()
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        Path(config_path).unlink()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        Path(config_path).unlink()
        return False


def main():
    """Main test function."""
    print("🔍 Continue CLI Debug Test")
    
    # Test models
    models = [
        "qwen3-coder:30b",
        "gpt-oss:20b"
    ]
    
    results = []
    for model in models:
        success = test_cn_with_model(model)
        results.append((model, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    for model, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {model}")
    
    passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {passed}/{len(results)} passed")


if __name__ == "__main__":
    main()