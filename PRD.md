# PRD: 映画メタ情報の品質評価・改善ループシステム

## 概要

既存の映画メタ情報取得システムにLLM as a Judgeを組み合わせ、取得したメタデータの品質を自動評価し、基準を満たすまで改善を繰り返すシステムを構築します。Direct Assessment方式で各項目を0.0〜5.0のスコアで評価し、すべての項目が3.5以上になるまで（最大3回）メタデータの精度向上を試みます。

## 目標

- 映画メタ情報の各項目（japanese_titles, distributor, box_office, cast, music, voice_actors）を個別に評価できるようにする
- LLMによる改善提案を基に、メタデータの精度を段階的に向上させる
- すべての項目が3.5以上のスコアを獲得するまで自動的に改善を繰り返す
- 各イテレーションの評価結果とメタデータをJSON形式で記録する
- 無限ループを防ぐため、最大3回のイテレーションで処理を終了する

## ユーザーストーリー

### US-001: メタデータ品質評価用のデータモデルを定義

**説明：** 開発者として、メタデータの各項目を評価するための構造化されたデータモデルが必要である。これにより、評価結果を型安全に扱える。

**受け入れ基準：**
- [x] `MetadataFieldScore`モデルを作成（field_name, score, reasoning）
- [x] `MetadataEvaluationResult`モデルを作成（iteration, field_scores, overall_status, improvement_suggestions）
- [x] `RefinementHistoryEntry`モデルを作成（iteration, metadata, evaluation）
- [x] `MetadataRefinementResult`モデルを作成（final_metadata, history, success, total_iterations）
- [x] `MetadataEvaluationOutput`モデルを作成（LLM出力用、field_scoresとimprovement_suggestionsを含む）
- [x] すべてのモデルが`movie_metadata/models.py`に追加される
- [x] 型チェックが通過すること

### US-002: メタデータ評価機能を実装

**説明：** 開発者として、MovieMetadataの各項目をLLM as a Judge（Direct Assessment）で評価する機能が必要である。これにより、データ品質を定量的に測定できる。

**受け入れ基準：**
- [x] `MetadataEvaluator`クラスを`movie_metadata/evaluator.py`に作成
- [x] `evaluate(metadata: MovieMetadata) -> MetadataEvaluationResult`メソッドを実装
- [x] 評価対象フィールド: japanese_titles, distributor, box_office, cast, music, voice_actors
- [x] 各フィールドを0.0〜5.0のスコアで評価（Direct Assessment形式）
- [x] GenAIClientを使用してLLM評価を実行
- [x] スコアが3.5未満のフィールドに対する改善提案を含める
- [x] 型チェックが通過すること

### US-003: メタデータ改善提案生成機能を実装

**説明：** 開発者として、評価結果に基づいてメタデータの改善方法を提案する機能が必要である。これにより、次のイテレーションで精度向上を図れる。

**受け入れ基準：**
- [x] `ImprovementProposer`クラスを`movie_metadata/improvement_proposer.py`に作成
- [x] `propose(movie_input: MovieInput, current_metadata: MovieMetadata, evaluation: MetadataEvaluationResult) -> str`メソッドを実装
- [x] スコアが3.5未満のフィールドに対する具体的な改善指示を生成
- [x] 改善指示には検索クエリの変更案や情報源の指定を含む
- [x] GenAIClientを使用してLLMで改善提案を生成
- [x] 型チェックが通過すること

### US-004: メタデータ再取得・改善機能を実装

**説明：** 開発者として、改善提案を反映してメタデータを再取得する機能が必要である。これにより、評価スコアを向上させることができる。

**受け入れ基準：**
- [x] `MovieMetadataFetcher`に`fetch_with_improvement(movie_input: MovieInput, improvement_instruction: str) -> MovieMetadata`メソッドを追加
- [x] 改善提案をプロンプトに組み込んでGoogle Searchで再検索
- [x] 既存の`fetch`メソッドとの共通ロジックを適切に抽出
- [x] 型チェックが通過すること

### US-005: 評価・改善ループ統合機能を実装

**説明：** 開発者として、評価→改善提案→再取得のサイクルを自動的に繰り返す機能が必要である。これにより、すべての項目が基準を満たすまで処理を継続できる。

**受け入れ基準：**
- [x] `MetadataRefiner`クラスを`movie_metadata/refiner.py`に作成
- [x] `refine(movie_input: MovieInput, max_iterations: int = 3, threshold: float = 3.5) -> MetadataRefinementResult`メソッドを実装
- [x] すべてのフィールドスコアが3.5以上になったら成功として終了
- [x] 最大3回のイテレーションで打ち切り
- [x] 各イテレーションの履歴（メタデータと評価結果）を記録
- [x] rate_limit_sleepを適切に適用
- [x] 型チェックが通過すること

### US-006: 結果出力機能を実装

**説明：** 開発者として、各イテレーションのスコアとメタデータをJSON形式で保存する機能が必要である。これにより、改善プロセスを追跡・分析できる。

**受け入れ基準：**
- [x] `RefinementResultWriter`クラスを`movie_metadata/refinement_writer.py`に作成
- [x] `write(result: MetadataRefinementResult, output_path: Path) -> None`メソッドを実装
- [x] 出力ファイル名は`{title}_refinement_{timestamp}.json`形式
- [x] JSON出力には各イテレーションのメタデータとスコアを含む
- [x] 最終的な成功/失敗ステータスを記録
- [x] 型チェックが通過すること

### US-007: メインスクリプトを作成

**説明：** ユーザーとして、コマンドラインから映画メタ情報の評価・改善ループを実行できるスクリプトが欲しい。これにより、システム全体の動作を確認できる。

**受け入れ基準：**
- [x] `main_refine.py`を作成
- [x] CSVから単一の映画情報を読み込み
- [x] MetadataRefinerを使用して評価・改善ループを実行
- [x] RefinementResultWriterで結果を保存
- [x] 各イテレーションの進捗をログ出力
- [x] 最終結果（成功/失敗、イテレーション数、各フィールドのスコア）をコンソールに表示
- [x] 型チェックが通過すること
- [x] `uv run main_refine.py`で実行可能なことを確認する

## 対象外事項

- 複数映画の一括処理機能は実装しない（単一映画の処理に集中）
- 既存のmain.pyへの統合は行わない（独立したモジュールとして実装）
- Web UIやダッシュボードは提供しない
- 評価基準のカスタマイズ機能は実装しない（閾値3.5固定）
- 人間によるレビュー・承認プロセスは含めない
- イテレーション回数の動的調整は行わない（最大3回固定）

## 技術的考慮事項

- 既存の`GenAIClient`、`MovieMetadataFetcher`、`MovieInput`、`MovieMetadata`を再利用する
- LLM as a Judgeの実装は`llm_judge/direct_assessment.py`のパターンを参考にする
- すべての新規コードは`movie_metadata_refine/`ディレクトリ内に配置する
- Ruffとtyの設定に従ってコード品質を維持する
- rate_limit_sleepを適切に適用してAPI制限を遵守する
- ログレベルはINFOで主要な処理フローを記録する
