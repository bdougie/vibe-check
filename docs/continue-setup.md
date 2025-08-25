# Continue Setup Guide for Vibe Check

Complete setup guide for configuring Continue extension with Vibe Check benchmarking framework.

## Quick Setup

### 1. Install Continue Extension

1. Open VS Code
2. Go to Extensions (Cmd+Shift+X / Ctrl+Shift+X)
3. Search for "Continue"
4. Install the Continue extension by Continue.dev

### 2. Configure Your First Model

Open Continue settings:
- Mac: `Cmd+Shift+P` → "Continue: Open Settings"
- Windows/Linux: `Ctrl+Shift+P` → "Continue: Open Settings"

Add a model configuration:

```json
{
  "models": [
    {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "apiKey": "YOUR_API_KEY"
    }
  ]
}
```

### 3. Test Your Setup

1. Open any code file
2. Select some code
3. Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)
4. Ask: "Explain this code"
5. Verify you get a response

## Model Configurations

### Ollama (Local Models)

```json
{
  "models": [
    {
      "title": "Qwen 2.5 Coder",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b"
    },
    {
      "title": "DeepSeek Coder",
      "provider": "ollama",
      "model": "deepseek-coder:6.7b"
    },
    {
      "title": "CodeLlama",
      "provider": "ollama",
      "model": "codellama:13b"
    }
  ]
}
```

### OpenAI

```json
{
  "models": [
    {
      "title": "GPT-4",
      "provider": "openai",
      "model": "gpt-4-turbo-preview",
      "apiKey": "YOUR_OPENAI_KEY"
    },
    {
      "title": "GPT-3.5 Turbo",
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "apiKey": "YOUR_OPENAI_KEY"
    }
  ]
}
```

### Anthropic Claude

```json
{
  "models": [
    {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "apiKey": "YOUR_ANTHROPIC_KEY"
    },
    {
      "title": "Claude 3 Haiku",
      "provider": "anthropic",
      "model": "claude-3-haiku-20240307",
      "apiKey": "YOUR_ANTHROPIC_KEY"
    }
  ]
}
```

## Benchmarking Configuration

### Optimal Settings for Benchmarking

```json
{
  "models": [...],
  "tabAutocompleteModel": {
    "title": "Qwen 2.5 Coder 1.5B",
    "provider": "ollama",
    "model": "qwen2.5-coder:1.5b"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "customCommands": [
    {
      "name": "benchmark",
      "prompt": "You are being benchmarked. Be concise and accurate.",
      "description": "Benchmark mode"
    }
  ],
  "contextProviders": [
    {
      "name": "code",
      "params": {}
    },
    {
      "name": "docs",
      "params": {}
    }
  ]
}
```

### Performance Tuning

For faster responses during benchmarking:

```json
{
  "models": [...],
  "requestOptions": {
    "timeout": 30000,
    "maxRetries": 2
  },
  "completionOptions": {
    "temperature": 0.2,
    "maxTokens": 2000,
    "topP": 0.95
  }
}
```

## Continue Keyboard Shortcuts

### Essential Shortcuts

| Action | Mac | Windows/Linux |
|--------|-----|---------------|
| Open Continue | `Cmd+L` | `Ctrl+L` |
| New Chat | `Cmd+Shift+L` | `Ctrl+Shift+L` |
| Toggle Sidebar | `Cmd+Shift+R` | `Ctrl+Shift+R` |
| Accept Suggestion | `Tab` | `Tab` |
| Reject Suggestion | `Esc` | `Esc` |

### Custom Shortcuts for Benchmarking

Add to VS Code keybindings.json:

```json
[
  {
    "key": "cmd+shift+b",
    "command": "continue.benchmark",
    "when": "editorTextFocus"
  },
  {
    "key": "cmd+shift+m",
    "command": "continue.metrics",
    "when": "editorTextFocus"
  }
]
```

## Multiple Model Setup

### Switching Models During Benchmarks

Configure multiple models to test:

```json
{
  "models": [
    {
      "title": "Claude (Benchmark)",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "apiKey": "KEY_1"
    },
    {
      "title": "GPT-4 (Benchmark)",
      "provider": "openai",
      "model": "gpt-4-turbo-preview",
      "apiKey": "KEY_2"
    },
    {
      "title": "Local Qwen (Benchmark)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b"
    }
  ],
  "modelRoles": {
    "default": "Claude (Benchmark)",
    "summarize": "GPT-4 (Benchmark)",
    "edit": "Local Qwen (Benchmark)"
  }
}
```

### Model Selection Strategy

1. Use the model dropdown in Continue sidebar
2. Or use `@model` syntax in chat:
   ```
   @claude Help me fix this bug
   @gpt-4 Review this code
   @qwen Refactor this function
   ```

## Integration with Vibe Check

### Enable Session Tracking

Continue automatically logs interactions when Vibe Check session tracking is active:

```bash
# Start tracking
uv run benchmark/continue_session_tracker.py --start

# Continue will now log all interactions
# Check status
uv run benchmark/continue_session_tracker.py --status
```

### Session Data Collection

Continue provides these metrics to Vibe Check:
- Prompt text and timestamps
- Model responses
- Response latency
- Token usage (if available)
- Error messages
- Code selections and edits

### Privacy Settings

Control what data is collected:

```json
{
  "telemetry": false,
  "anonymousUsageTracking": false,
  "viberCheckIntegration": {
    "enabled": true,
    "collectPrompts": true,
    "collectResponses": true,
    "collectTimings": true,
    "collectErrors": true
  }
}
```

## Troubleshooting

### Continue Not Responding

1. Check VS Code Output panel → Continue
2. Verify model configuration
3. Test API keys:
   ```bash
   # For OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_KEY"
   
   # For Anthropic
   curl https://api.anthropic.com/v1/models \
     -H "x-api-key: YOUR_KEY"
   ```

### Ollama Connection Issues

```bash
# Check Ollama is running
ollama list

# Start Ollama if needed
ollama serve

# Pull required model
ollama pull qwen2.5-coder:7b

# Test model
ollama run qwen2.5-coder:7b "Hello"
```

### Session Not Recording

1. Verify tracking is started:
   ```bash
   uv run benchmark/continue_session_tracker.py --status
   ```

2. Check Continue is configured:
   ```bash
   cat ~/.continue/config.json
   ```

3. Review session logs:
   ```bash
   tail -f benchmark/results/sessions/latest/debug.log
   ```

## Best Practices

### 1. Consistent Environment

- Use the same Continue version across benchmarks
- Keep model configurations identical
- Document any configuration changes

### 2. Model Temperature

For benchmarking consistency:
```json
{
  "completionOptions": {
    "temperature": 0.1  // Lower = more consistent
  }
}
```

### 3. Context Management

Limit context for faster responses:
```json
{
  "contextProviders": [
    {
      "name": "code",
      "params": {
        "maxLines": 100,
        "maxFiles": 5
      }
    }
  ]
}
```

### 4. Error Handling

Configure retry behavior:
```json
{
  "requestOptions": {
    "maxRetries": 3,
    "retryDelay": 1000,
    "timeout": 30000
  }
}
```

## Advanced Features

### Custom Commands

Create benchmark-specific commands:

```json
{
  "customCommands": [
    {
      "name": "fix",
      "prompt": "Fix the issue described in the task. Be precise.",
      "description": "Fix benchmark task"
    },
    {
      "name": "explain",
      "prompt": "Explain your solution step by step.",
      "description": "Explain approach"
    },
    {
      "name": "test",
      "prompt": "Write tests for the solution.",
      "description": "Generate tests"
    }
  ]
}
```

### Slash Commands

Use built-in commands during benchmarks:
- `/edit` - Edit selected code
- `/comment` - Add comments
- `/fix` - Fix problems
- `/explain` - Explain code
- `/test` - Generate tests

### Context Providers

Configure what Continue can see:

```json
{
  "contextProviders": [
    {
      "name": "codebase",
      "params": {
        "includePaths": ["src/", "tests/"],
        "excludePaths": ["node_modules/", ".git/"]
      }
    },
    {
      "name": "problems",
      "params": {
        "enabled": true
      }
    }
  ]
}
```

## Next Steps

1. Configure your preferred models
2. Run a test benchmark
3. Review the [Manual Benchmarking Guide](manual-benchmarking-guide.md)
4. Analyze results with [Session Analysis](session-analysis.md)

---

Need help? Check [Troubleshooting](#troubleshooting) or open an [issue](https://github.com/bdougie/vibe-check/issues).