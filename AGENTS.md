# Repository Guidelines

## 言語設定
- 会話は日本語で実施する
- 思考や実施して言うことも日本語で出力する

## プロジェクト概要
このリポジトリは Google Generative AI (google-genai) SDK を学習するための Python 3.14 プロジェクトです。依存関係は uv で管理し、コード品質は Ruff と Ty を使って確認します。すべてのコマンドは `app/` ディレクトリで実行します。

## Project Structure & Module Organization
- `app/` がメインアプリケーションです。
- `app/main.py` が実行エントリで、`app/movie_metadata/` にコアロジックがあります。
- `app/data/` に入力 CSV と出力 JSON の保存先があります（例: `app/data/movies.csv`, `app/data/output/`）。
- 設定は `app/ruff.toml`, `app/ty.toml`, `app/pyproject.toml` を参照します。

## Build, Test, and Development Commands
- `cd app && uv sync` 依存関係の同期。
- `cd app && uv run main.py` アプリケーション実行。
- `cd app && uv run ruff format .` フォーマット。
- `cd app && uv run ruff check .` リント。
- `cd app && uv run ty check` 型チェック。

## Coding Style & Naming Conventions
- インデントはスペース 4、行の長さは 88 文字。
- Python は snake_case、モジュールは `movie_metadata/` 配下に分割。
- 例: `csv_reader.py`, `metadata_fetcher.py`, `json_writer.py`。

## Testing Guidelines
- 専用のテストフレームワークは未導入です。
- 迅速な確認は `app/data/movies_test.csv` を使い、`uv run` のワンライナーを `app/README.md` の例に沿って実行します。
- テスト追加時は `app/tests/` を新設し、ファイル名は `test_*.py` を推奨します。

## Commit & Pull Request Guidelines
- コミットメッセージは日本語で簡潔に（例: `サンプルコードの作成`）。
- PR には変更概要、動作確認手順、影響範囲を記載してください。
- 生成データや API 仕様に変更がある場合は、サンプル出力や更新理由を添えてください。

## Security & Configuration Tips
- API キーは `GEMINI_API_KEY` として `.env` に設定します（`.env.example` を参照）。
- Google Search grounding は課金対象のため、テストは少数の件数で実施してください。

## 学習フロー補助
- ユーザーが「学習を開始します」と伝えた場合は `docs/llm_as_judge_plan.md` を読み込み、進捗管理セクションの「現在の進捗」を確認して次のStepから開始する。
