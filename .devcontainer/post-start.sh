#!/bin/bash
set -e

sudo cp .devcontainer/config/.claude/* ~/.claude/
sudo cp .devcontainer/config/.tmux.conf ~/

sudo chown -R vscode:vscode /home/vscode/.claude /home/vscode/.tmux.conf