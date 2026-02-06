#!/bin/bash
set -e

sudo chown -R vscode:vscode /home/vscode/.claude /home/vscode/.codex /home/vscode/.gemini /home/vscode/.tmux

curl -fsSL https://claude.ai/install.sh | bash
npm install -g @openai/codex 
npm install -g @google/gemini-cli 

if [ ! -d ~/.tmux/plugins/tpm ]; then
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi