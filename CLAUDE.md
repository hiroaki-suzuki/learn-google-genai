# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

[Google Generative AI (google-genai)](https://googleapis.github.io/python-genai/) SDKの学習用リポジトリです。Python 3.14を使用し、[uv](https://docs.astral.sh/uv/)パッケージマネージャーで依存関係を管理しています。

## 開発環境

- **Python**: 3.14 (ty.toml で管理)
- **パッケージマネージャー**: [uv](https://docs.astral.sh/uv/)
- **主要な依存関係**: [google-genai](https://googleapis.github.io/python-genai/) (>=1.61.0)
- **開発ツール**: [Ruff](https://docs.astral.sh/ruff/) (linter/formatter)、[Ty](https://docs.astral.sh/ty/) (型チェッカー)

## セットアップ

開発環境はDevContainerで構成されており、自動的にセットアップされます。

## 基本コマンド

### アプリケーション実行

```bash
cd app
uv run main.py
```

### コード品質チェック

```bash
cd app
uv run ruff format .                                     # フォーマット
uv run ruff check .                                      # リント
uv run ruff check --fix .                                # リント自動修正
uv run ruff check --fix --unsafe-fixes .                 # 危険な修正も含む
uv run ty check                                          # 型チェック
```

統合チェック(フォーマット、リント修正、型チェック):

```bash
cd app
uv run ruff format . && uv run ruff check --fix . && uv run ty check
```

## プロジェクト構造

```
learn-google-genai/
├── app/                      # メインアプリケーション
│   ├── main.py
│   ├── pyproject.toml       # 依存関係
│   ├── ruff.toml           # Ruff設定
│   └── .env                # 環境変数 (.env.example参照)
└── .devcontainer/
```

## コーディング規約

- **Python**: 3.14
- **行の長さ**: 88文字
- **インデント**: スペース4つ
- **`__init__.py`**: F401エラー(未使用インポート)を無視

## 環境変数

`.env.example` をコピーして `.env` を作成。uvが自動的に読み込みます。

## 注意事項

- すべてのコマンドは `app/` ディレクトリ内で実行
- スクリプト実行は `uv run` を使用
