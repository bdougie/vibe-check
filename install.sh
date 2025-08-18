#!/bin/bash
# Vibe CLI Installation Script

set -e

echo "🚀 Installing Vibe CLI..."

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a symlink to the wrapper script in /usr/local/bin
if [ -w "/usr/local/bin" ]; then
    echo "📦 Installing to /usr/local/bin/vibe..."
    ln -sf "$SCRIPT_DIR/vibe-wrapper.sh" /usr/local/bin/vibe
    echo "✅ Installed successfully!"
    echo ""
    echo "You can now use: vibe --help"
else
    # Try user's local bin
    mkdir -p "$HOME/.local/bin"
    echo "📦 Installing to ~/.local/bin/vibe..."
    ln -sf "$SCRIPT_DIR/vibe-wrapper.sh" "$HOME/.local/bin/vibe"
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo ""
        echo "⚠️  Please add ~/.local/bin to your PATH:"
        echo ""
        echo "Add this line to your ~/.bashrc or ~/.zshrc:"
        echo 'export PATH="$HOME/.local/bin:$PATH"'
        echo ""
        echo "Then reload your shell or run: source ~/.bashrc"
    else
        echo "✅ Installed successfully!"
        echo ""
        echo "You can now use: vibe --help"
    fi
fi

echo ""
echo "📝 Example usage:"
echo "  vibe --list-challenges"
echo "  vibe --model qwen2.5-coder:7b --challenge easy"
echo "  vibe --model gpt-oss:20b --task basic_todo_app"
echo ""
echo "🎉 Installation complete!"