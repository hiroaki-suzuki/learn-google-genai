# PRD: movie_metadataモジュールのテストコード充実化

## 概要

movie_metadataパッケージの全11モジュールに対して包括的なテストコードを作成し、コードカバレッジを90%以上に引き上げます。現在、4つのモジュールにのみテストが存在し、残り7つのモジュールにはテストが未作成です。すべての外部依存をモック化し、各ストーリー完了時にカバレッジを確認しながら段階的にテストを充実させます。

## 目標

- 全11モジュールに対して包括的な単体テストを作成する
- プロジェクト全体のコードカバレッジを90%以上に到達させる
- pytest-covを使用してカバレッジを継続的に測定できる環境を構築する
- すべての外部依存（GenAI API、ファイルI/O）を適切にモック化する
- 主要な例外パターン（ValueError, FileNotFoundError, APIError等）をテストする

## ユーザーストーリー

### US-001: pytest-covの依存関係追加とカバレッジ測定環境の構築

**説明:** 開発者として、コードカバレッジを継続的に測定できるよう、pytest-covをプロジェクトに追加したい。

**受け入れ基準:**
- [x] pyproject.tomlのdev依存関係にpytest-covを追加する
- [x] `uv run pytest --cov=movie_metadata --cov-report=term-missing`コマンドが正常に実行できる
- [x] 現在のカバレッジベースラインを確認し、progress.txtに記録する
- [x] 型チェックが通過する

### US-002: models.pyのバリデーションテスト作成

**説明:** 開発者として、Pydanticモデルのバリデーション機能が正しく動作することを確認するため、test_models.pyを作成したい。

**受け入れ基準:**
- [x] tests/test_models.pyファイルを作成する
- [x] MovieInput, MovieMetadata, MetadataFieldScore, MetadataEvaluationResult, RefinementHistoryEntry, MetadataRefinementResultの正常系テストを実装する
- [x] フィールドのバリデーション（score範囲0.0-5.0など）の異常系テストを実装する
- [x] `uv run pytest tests/test_models.py -v`が成功する
- [x] models.pyのカバレッジを確認し、progress.txtに記録する
- [x] 型チェックが通過する

### US-003: prompts.pyの単体テスト作成

**説明:** 開発者として、プロンプト生成関数が正しく動作することを確認するため、test_prompts.pyを作成したい。

**受け入れ基準:**
- [x] tests/test_prompts.pyファイルを作成する
- [x] build_metadata_fetch_prompt関数のテスト（通常版、改善指示付き版）を実装する
- [x] build_metadata_evaluation_prompt関数のテストを実装する
- [x] build_improvement_proposal_prompt関数のテストを実装する
- [x] 各関数の戻り値が期待される文字列形式であることを確認する
- [x] `uv run pytest tests/test_prompts.py -v`が成功する
- [x] prompts.pyのカバレッジを確認し、progress.txtに記録する
- [x] 型チェックが通過する

### US-004: metadata_fetcher.pyの単体テスト作成（モック使用）

**説明:** 開発者として、GenAI APIを実際に呼び出すことなくメタデータ取得機能をテストするため、test_metadata_fetcher.pyを作成したい。

**受け入れ基準:**
- [x] tests/test_metadata_fetcher.pyファイルを作成する
- [x] GenAIClientをモック化し、fetch()メソッドの正常系テストを実装する
- [x] fetch_with_improvement()メソッドの正常系テストを実装する
- [x] APIエラー時（ClientError, ServerError, APIError）の異常系テストを実装する
- [x] 空のレスポンス時のデフォルト値返却テストを実装する
- [x] `uv run pytest tests/test_metadata_fetcher.py -v`が成功する
- [x] metadata_fetcher.pyのカバレッジを確認し、progress.txtに記録する
- [x] 型チェックが通過する

### US-005: evaluator.pyの単体テスト作成（モック使用）

**説明:** 開発者として、メタデータ評価機能をテストするため、test_evaluator.pyを作成したい。

**受け入れ基準:**
- [x] tests/test_evaluator.pyファイルを作成する
- [x] GenAIClientをモック化し、evaluate()メソッドの正常系テストを実装する
- [x] すべてのフィールドが3.5以上の場合のoverall_status="pass"テストを実装する
- [x] 1つ以上のフィールドが3.5未満の場合のoverall_status="fail"テストを実装する
- [x] API呼び出し失敗時の例外処理テストを実装する
- [x] `uv run pytest tests/test_evaluator.py -v`が成功する
- [x] evaluator.pyのカバレッジを確認し、progress.txtに記録する
- [x] 型チェックが通過する

### US-006: improvement_proposer.pyの単体テスト作成（モック使用）

**説明:** 開発者として、改善提案生成機能をテストするため、test_improvement_proposer.pyを作成したい。

**受け入れ基準:**
- [x] tests/test_improvement_proposer.pyファイルを作成する
- [x] GenAIClientをモック化し、propose()メソッドの正常系テストを実装する
- [x] overall_status="pass"の場合に"改善の必要なし"を返すテストを実装する
- [x] overall_status="fail"の場合に改善提案を生成するテストを実装する
- [x] API呼び出し失敗時の例外処理テストを実装する
- [x] `uv run pytest tests/test_improvement_proposer.py -v`が成功する
- [x] improvement_proposer.pyのカバレッジを確認し、progress.txtに記録する
- [x] 型チェックが通過する

### US-007: refinement_writer.pyの単体テスト作成（モック使用）

**説明:** 開発者として、改善履歴のJSON出力機能をテストするため、test_refinement_writer.pyを作成したい。

**受け入れ基準:**
- [ ] tests/test_refinement_writer.pyファイルを作成する
- [ ] RefinementWriterクラスのwrite()メソッドの正常系テストを実装する（tmp_pathを使用）
- [ ] 出力されたJSONファイルの内容検証テストを実装する
- [ ] ディレクトリが存在しない場合の自動作成テストを実装する
- [ ] ファイル書き込み失敗時の例外処理テストを実装する
- [ ] `uv run pytest tests/test_refinement_writer.py -v`が成功する
- [ ] refinement_writer.pyのカバレッジを確認し、progress.txtに記録する
- [ ] 型チェックが通過する

### US-008: refiner.pyの統合テスト作成（モック使用）

**説明:** 開発者として、メタデータ改善ループ全体の動作をテストするため、test_refiner.pyを作成したい。

**受け入れ基準:**
- [ ] tests/test_refiner.pyファイルを作成する
- [ ] GenAIClientをモック化し、refine()メソッドの正常系テスト（1イテレーションで成功）を実装する
- [ ] 複数イテレーションでの改善ループテストを実装する
- [ ] max_iterations到達時の失敗テストを実装する
- [ ] API呼び出し失敗時の例外処理テストを実装する
- [ ] `uv run pytest tests/test_refiner.py -v`が成功する
- [ ] refiner.pyのカバレッジを確認し、progress.txtに記録する
- [ ] 型チェックが通過する

### US-009: 既存テストのカバレッジ向上（csv_reader, json_writer）

**説明:** 開発者として、既存のテストのカバレッジを向上させるため、test_csv_reader.pyとtest_json_writer.pyに追加テストケースを実装したい。

**受け入れ基準:**
- [ ] test_csv_reader.pyに未カバーの分岐やエッジケースのテストを追加する
- [ ] test_json_writer.pyに未カバーの分岐やエッジケースのテストを追加する
- [ ] `uv run pytest tests/test_csv_reader.py tests/test_json_writer.py -v`が成功する
- [ ] csv_reader.pyとjson_writer.pyのカバレッジを確認し、progress.txtに記録する
- [ ] 型チェックが通過する

### US-010: 既存テストのカバレッジ向上（genai_client, metadata_service）

**説明:** 開発者として、既存のテストのカバレッジを向上させるため、test_genai_client.pyとtest_metadata_service.pyに追加テストケースを実装したい。

**受け入れ基準:**
- [ ] test_genai_client.pyに未カバーの分岐やエッジケースのテストを追加する
- [ ] test_metadata_service.pyに未カバーの分岐やエッジケースのテストを追加する
- [ ] `uv run pytest tests/test_genai_client.py tests/test_metadata_service.py -v`が成功する
- [ ] genai_client.pyとmetadata_service.pyのカバレッジを確認し、progress.txtに記録する
- [ ] 型チェックが通過する

### US-011: 全体カバレッジ90%達成の確認と最終調整

**説明:** 開発者として、プロジェクト全体のコードカバレッジが90%以上であることを確認し、必要に応じて追加テストを実装したい。

**受け入れ基準:**
- [ ] `uv run pytest --cov=movie_metadata --cov-report=term-missing --cov-report=html`を実行する
- [ ] プロジェクト全体のカバレッジが90%以上であることを確認する
- [ ] 90%未満の場合、不足しているモジュールに追加テストを実装する
- [ ] すべてのテストが成功することを確認する（`uv run pytest tests/ -v`）
- [ ] 最終的なカバレッジレポートをprogress.txtに記録する
- [ ] 型チェックが通過する

## 対象外項目

- 実際のGenAI APIを使用した統合テスト（すべてモック化で対応）
- パフォーマンステスト、負荷テスト
- E2Eテスト（main.pyからの実行テスト）
- カバレッジ100%の達成（90%以上で十分とする）
- CI/CDパイプラインへのカバレッジチェック組み込み（本プロジェクトの範囲外）
- テストデータの自動生成やファクトリパターンの導入

## 技術的考慮事項

- pytest-mockを使用してGenAIClientをモック化する
- tmp_pathフィクスチャを使用してファイルI/Oテストを実施する
- conftest.pyで共通のフィクスチャを定義し、テストコードの重複を避ける
- カバレッジレポートは各ストーリー完了時に該当モジュールを確認し、最終的に全体で90%を達成する
- 既存のconftest.pyに定義されているフィクスチャを活用する

## 依存関係

- Python 3.14
- pytest >= 8.0.0
- pytest-mock >= 3.12.0
- pytest-cov（US-001で追加）
- google-genai >= 1.61.0
- pydantic-settings >= 2.0.0
