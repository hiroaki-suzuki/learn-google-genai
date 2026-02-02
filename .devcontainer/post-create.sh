#!/bin/bash
set -e

sudo chown -R vscode:vscode /home/vscode/.claude /home/vscode/.codex /home/vscode/.gemini

curl -fsSL https://claude.ai/install.sh | bash
npm install -g @openai/codex 
npm install -g @google/gemini-cli 