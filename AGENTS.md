# Repository Guidelines

## プロジェクト概要
Google Generative AI (google-genai) SDK の学習用リポジトリです。CSV の映画データを取得し、Google Search grounding で補完して JSON を出力します。主要な実装は `app/` 配下にあります。

## Project Structure & Module Organization
- `app/`: アプリ本体と依存関係 (`app/pyproject.toml`)
- `app/movie_metadata/`: CSV 読み込み、メタ情報取得、JSON 出力のコアロジック
- `app/llm_judge/`: 評価/改善ループ関連ロジック
- `app/tests/`: pytest テスト (`test_*.py`)
- `app/data/`: サンプル CSV と出力 JSON
- `docs/`, `plans/`: 仕様・計画ドキュメント

## Build, Test, and Development Commands
すべて `app/` ディレクトリで実行します。
- `uv sync`: 依存関係のインストール/同期
- `uv run main.py`: メイン実行（映画データを処理）
- `uv run ruff format .`: フォーマット
- `uv run ruff check .`: リント
- `uv run ty check`: 型チェック
- `uv run pytest`: テスト実行

## Coding Style & Naming Conventions
- Python 3.14 / Ruff 設定: 行長 88、インデント 4 スペース、ダブルクォート
- PEP 8 ベースの命名（クラス `PascalCase`、関数/変数 `snake_case`）
- `__init__.py` は `F401` を無視（未使用インポート許容）

## Testing Guidelines
- フレームワーク: `pytest`（`pytest-mock`, `pytest-cov` あり）
- テスト配置: `app/tests/`、命名: `test_*.py`
- 重要ロジックは例外系と境界値もカバーすること

## Commit & Pull Request Guidelines
- コミットは Conventional Commits 形式を使用（例: `feat: ... (US-001)`, `docs: ...`）
- 変更理由と影響範囲が分かる説明を付ける
- PR には概要、テスト結果、関連チケット番号を記載

## Security & Configuration Tips
- `GEMINI_API_KEY` を環境変数に設定（`.env` 利用想定）
- API クォータに注意し、少量データで動作確認すること
