# Continue Configuration Generator

The Continue Configuration Generator automatically creates a `config.yaml` file for the [Continue](https://continue.dev) VS Code extension based on available models and user preferences.

## Overview

Continue is an AI-powered coding assistant that integrates with VS Code. The configuration generator:

- Detects locally installed Ollama models
- Adds templates for commercial models (OpenAI, Anthropic)
- Configures context providers and commands
- Sets up autocomplete preferences
- Saves configuration to `~/.continue/config.yaml`

## Usage

### Running the Generator

```bash
uv run benchmark/continue_config_generator.py
```

The generator will:

1. **Check for existing configuration** - Prompts to overwrite if one exists
2. **Detect Ollama models** - Automatically finds all locally installed models
3. **Configure commercial models** - Optionally add API keys for OpenAI/Anthropic
4. **Generate complete config** - Creates a ready-to-use configuration file
5. **Save to ~/.continue** - Places the config in the correct location

### Interactive Prompts

During setup, you'll be asked:

```
Do you have an OpenAI API key to configure? (y/n): 
Enter your OpenAI API key: 

Do you have an Anthropic API key to configure? (y/n):
Enter your Anthropic API key: 
```

You can skip these and add API keys later by editing the config file directly.

## Configuration Structure

### Generated config.yaml

```yaml
name: Continue Configuration
version: 1.0
schema: 1.0.0

models:
  # Ollama models (auto-detected)
  - name: Ollama codestral
    provider: ollama
    model: codestral
    roles: 
      - chat
      - autocomplete
      - edit
    autocompleteOptions:
      debounceDelay: 250
      maxPromptTokens: 2048
      prefixPercentage: 0.5

  # Commercial models
  - name: GPT-4
    provider: openai
    model: gpt-4
    apiKey: YOUR_OPENAI_API_KEY
    roles: 
      - chat
      - edit
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 2048

  - name: Claude 3.5 Sonnet
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    apiKey: YOUR_ANTHROPIC_API_KEY
    roles: 
      - chat
      - edit
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 4096

# Autocomplete settings
tabAutocompleteModel:
  title: Ollama codestral
  provider: ollama
  model: codestral

# Context providers
contextProviders:
  - name: code
  - name: docs
  - name: diff
  - name: terminal
  - name: problems
  - name: folder
  - name: codebase

# Slash commands
slashCommands:
  - name: edit
    description: Edit selected code
  - name: comment
    description: Write comments for the selected code
  - name: share
    description: Export the current chat session to markdown
  - name: cmd
    description: Generate a shell command
  - name: commit
    description: Generate a git commit message

# Custom commands
customCommands:
  - name: test
    prompt: Write comprehensive unit tests for the selected code
    description: Generate unit tests
  - name: check
    prompt: Review the selected code for potential bugs, security issues, and improvements
    description: Perform code review
  - name: benchmark
    prompt: Analyze the performance of the selected code and suggest optimizations
    description: Performance analysis
```

## Model Detection

### Ollama Models

The generator automatically detects Ollama models by running `ollama list`. Models are categorized by their capabilities:

- **Code-focused models** (codestral, deepseek-coder): Enabled for chat, autocomplete, and edit
- **General models** (llama2, mistral): Enabled for chat and edit
- **Other models**: Enabled for chat only

The first code-focused model found is set as the default autocomplete model.

### Commercial Models

Templates are added for:

- **OpenAI**: GPT-4 configuration
- **Anthropic**: Claude 3.5 Sonnet configuration

API keys can be added during setup or manually edited later.

## Manual Configuration

### Adding API Keys

Edit `~/.continue/config.yaml` and replace placeholder keys:

```yaml
# Replace these with your actual keys
apiKey: YOUR_OPENAI_API_KEY    → apiKey: sk-your-actual-key
apiKey: YOUR_ANTHROPIC_API_KEY → apiKey: sk-ant-your-actual-key
```

### Adding New Models

Add entries to the `models` section:

```yaml
models:
  - name: Custom Model
    provider: provider_name
    model: model_name
    apiKey: your_api_key  # if required
    roles: 
      - chat
      - edit
```

### Changing Autocomplete Model

Modify the `tabAutocompleteModel` section:

```yaml
tabAutocompleteModel:
  title: Your Preferred Model
  provider: provider_name
  model: model_name
```

## File Locations

- **Configuration**: `~/.continue/config.yaml`
- **Backup** (if exists): `~/.continue/config.yaml.backup`
- **Generator script**: `benchmark/continue_config_generator.py`

## Troubleshooting

### Ollama Not Detected

If Ollama models aren't detected:

1. Ensure Ollama is installed: `ollama --version`
2. Check Ollama service is running: `ollama list`
3. Pull models if needed: `ollama pull codestral`

### Configuration Not Loading

After generating the configuration:

1. Restart VS Code
2. Reload the Continue extension
3. Check Continue output panel for errors

### Invalid API Keys

If API keys are invalid:

1. Check for typos in the keys
2. Ensure keys have proper permissions
3. Verify billing/credits are available

## Dependencies

The configuration generator requires:

- Python 3.8+
- PyYAML (`uv pip install pyyaml`)
- Ollama (optional, for local models)

## Integration with Benchmarks

The Continue configuration integrates with the vibe-check benchmark framework:

1. Configure Continue with your preferred models
2. Run benchmarks to test model performance
3. Use benchmark results to optimize model selection
4. Update Continue config based on benchmark findings

## Related Documentation

- [Continue Documentation](https://docs.continue.dev/reference)
- [Ollama Setup Guide](ollama.md)
- [Model Selection Guide](models.md)
- [Benchmark Task Runner](../README.md#running-benchmarks)

## Example Workflow

1. **Install Ollama and pull models**:
   ```bash
   ollama pull codestral
   ollama pull llama2
   ```

2. **Run the configuration generator**:
   ```bash
   uv run benchmark/continue_config_generator.py
   ```

3. **Add API keys** (if using commercial models):
   - Enter during setup, or
   - Edit `~/.continue/config.yaml` manually

4. **Restart VS Code** to load the new configuration

5. **Test with Continue**:
   - Open a code file
   - Use `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux) to open Continue chat
   - Try autocomplete with Tab
   - Use slash commands like `/edit` or `/comment`

## Security Notes

- API keys are stored in plain text in the config file
- Ensure `~/.continue/config.yaml` has appropriate file permissions
- Never commit config files with real API keys to version control
- Consider using environment variables for sensitive keys in production