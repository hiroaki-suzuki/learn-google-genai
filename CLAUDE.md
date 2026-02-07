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

### テスト実行

```bash
cd app
uv run pytest                                            # 全テスト実行
uv run pytest -v                                         # 詳細出力
uv run pytest --cov                                      # カバレッジ付き実行
uv run pytest tests/test_config.py                       # 特定のテストファイル
```

**注意**: `pytest.ini`により、テスト実行時は自動的に`ENV=test`が設定され、`.env.test`ファイルが読み込まれます。

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

### 環境変数ファイルの種類

- **`.env`**: 本番環境用の設定（`ENV=production`または未設定時に使用）
- **`.env.test`**: テスト環境用の設定（`ENV=test`時に使用）
- **`.env.example`**: 環境変数の設定例とドキュメント

`.env.example` をコピーして `.env` を作成。uvが自動的に読み込みます。

### 環境切り替え

`ENV`環境変数で使用する環境変数ファイルを切り替えられます:

```bash
# 本番環境（デフォルト）
uv run main.py

# テスト環境（pytestが自動設定）
ENV=test uv run main.py
```

## 注意事項

- すべてのコマンドは `app/` ディレクトリ内で実行
- スクリプト実行は `uv run` を使用
