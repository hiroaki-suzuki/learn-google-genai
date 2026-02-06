# LLM as a Judge向け Pythonライブラリ候補（映画メタデータ正確性評価）

## 目的
`app/main.py` のように取得した映画メタデータ（出演者、監督、公開年、ジャンルなど）が正しいかを評価する用途において、2026年時点で利用しやすく、Geminiに対応し、かつ利用が広い（または増加傾向にある）Pythonライブラリを5件に絞って整理する。

## 選定基準
1. Gemini対応（`google-genai` または Vertex AI 経由で利用可能）
2. 事実性/正確性評価（factuality/correctness/verification）に適する
3. 導入の容易さ
4. 人気/利用増加の根拠（PyPI統計・公式ドキュメント・公開リポジトリの継続更新）

注: PyPIのダウンロード統計は pypistats のAPI/ページで取得できたもののみ記載。

## 候補サマリ
| ライブラリ | 主用途 | Gemini対応 | 事実性評価の適性 | 自律改善ループ適性 | 使い方の簡単さ | 人気/増加の根拠 |
| --- | --- | --- | --- | --- | --- | --- |
| `google-genai` | Gemini SDK（基盤） | 公式SDK（Gemini Dev API/Vertex AI両対応） | 自前でJudge実装 | 高 | 非常に簡単 | PyPIダウンロード数が大きい。 |
| `google-adk` | エージェント開発/評価/デプロイ | Gemini最適化のエージェント基盤。 | エージェント評価機能を含む。 | 高 | 中 | 公式リリースが高頻度（概ね隔週）。 |
| `ragas` | 評価フレームワーク | Gemini統合手順あり。 | 参照付きのFactualCorrectness指標がある。 | 低〜中 | 中 | 公式ドキュメントにGemini統合が明記。 |
| `langchain` + `langsmith` | 評価/観測基盤 | `langchain-google-genai` がGemini Dev API/Vertex AIを両対応。 | LLM-as-judge評価の公式ガイドあり。 | 中 | 中 | PyPIダウンロード多数。 |
| `trulens` | 評価/トラッキング | Gemini Providerが公式に用意。 | フィードバック関数で評価指標を定義できる。 | 中〜高 | 中 | PyPIに直近リリースがある。 |

## 1. Google GenAI SDK (`google-genai`)
### 概要
Google Gen AI SDKは、Gemini Developer API と Vertex AI の両方をサポートする公式Python SDK。Python向けは `google-genai` として提供されている。

### 映画メタデータ評価への適用
「抽出したメタデータ」と「参照データ（正解）」をプロンプトに入れて、単一のLLM Judgeで正誤判定・理由・スコアを出す形が最もシンプル。SDK単体なので、評価ロジックを自由に作れる。

### Pros
- 公式SDKで最新仕様に追随しやすい。
- Gemini Developer API / Vertex AI を同一SDKで切り替え可能。
- PyPIダウンロード数が非常に大きく、利用が広い。

### Cons
- 事実性評価の指標や集計は自前実装が必要。
- 既存評価フレームワークほどのレポート機能はない。

### 自律改善ループ適性
- 取得→評価→再取得を最小構成で自作できるため、最も軽いループ実装に向く。

## 2. Agent Development Kit (`google-adk`)
### 概要
エージェントの構築・評価・デプロイに対応したGoogle公式のPythonツールキット。`pip install google-adk` で導入できる。

### 映画メタデータ評価への適用
「取得→検証→再取得」のような多段評価フローをエージェントとして構築しやすい。メタデータの正誤検証をツール化して評価に組み込む用途に向く。

### Pros
- エージェント評価やツール連携を前提にした設計。
- 公式リリースの更新頻度が高い（概ね隔週）。

### Cons
- 単純なJudge用途ではややオーバースペック。
- 学習コストは他の評価専用ライブラリより高め。

### 自律改善ループ適性
- エージェントが「再取得の必要性」を判断し、ツール呼び出しで再取得できるため、運用ループに最適。

## 3. Ragas (`ragas`)
### 概要
評価指標を中心に設計されたフレームワーク。Geminiは公式に統合手順が案内されている。

### 映画メタデータ評価への適用
参照データ（正解メタデータ）と抽出結果を比較し、「事実性の一致度」を数値化する用途に向く。`FactualCorrectness` 指標は、回答・参照を主張分解しNLIで重なりを評価する。

### Pros
- 参照付きの事実性評価が強力で、メタデータの正誤判定に適合。
- Gemini対応が公式に明記されている。

### Cons
- 評価対象の整形（参照データ）を事前に用意する必要がある。
- 使い方はSDK単体より複雑。

### 自律改善ループ適性
- 参照データがある場合は評価強化に有効だが、再取得のオーケストレーションは別実装が必要。

## 4. LangChain + LangSmith（`langchain-google-genai` + `langsmith`）
### 概要
LangChainでGeminiを使い、LangSmithでLLM-as-a-judge評価を実装・運用する構成。`langchain-google-genai` は `google-genai` SDKを利用し、Gemini Developer API と Vertex AI を両方サポートする。

### 映画メタデータ評価への適用
メタデータ正誤の判定テンプレートを作り、LangSmithの評価パイプラインに載せることで、評価結果の追跡・比較がしやすい。LangSmithにはLLM-as-judge評価の公式ガイドがある。

### Pros
- LangSmithがLLM-as-judgeの実装手順を公式に提供。
- `langchain-google-genai` は `google-genai` SDKに統合済みでGeminiに直結。
- PyPIダウンロード数が大きく、実運用利用が多い。

### Cons
- LangChain/LangSmithの概念を理解する学習コストあり。
- 依存関係が増えやすい。

### 自律改善ループ適性
- ループ自体は自作だが、評価ログの可視化や回帰検知に強い。

## 5. TruLens (`trulens`)
### 概要
LLMアプリの評価/追跡に特化したライブラリ。Google Gemini向けのProviderが公式に用意され、別途 `trulens-providers-google` をインストールする。

### 映画メタデータ評価への適用
メタデータ抽出の結果に対して、正確性や根拠の妥当性に関するフィードバック関数を作り、継続的に評価・比較できる。

### Pros
- Gemini用のProviderが明示されており、導入しやすい。
- PyPIに直近リリースがある。

### Cons
- 使い方は「評価設計前提」で、最小構成でも少し複雑。
- 目的に合わせたフィードバック関数設計が必要。

### 自律改善ループ適性
- フィードバック関数で「誤り検出」を作りやすく、再取得ループのスコアリングに使いやすい。

## 自律改善ループ（取得→評価→再取得→再評価）の設計方針
### 目的
映画メタデータの誤りを検知し、低スコア項目のみ再取得して改善する。最終的に一定の品質基準を満たしたら停止する。

### 簡易フロー
1. メタデータ取得（`app/main.py` 相当）
2. Judgeで検索再検証し、項目別スコアを付与
3. 低スコア項目のみ再取得（再プロンプト）
4. 再評価
5. 平均スコアが閾値以上 or 最大反復で停止

### ライブラリごとの実現方法
1. `google-genai`: Gemini SDKで「取得」「再取得」「Judge」を全部自前実装する最小構成。
2. `google-adk`: 取得/評価/再取得をツールとして分割し、エージェントが判断して実行。
3. `ragas`: 参照メタデータがある場合に、FactualCorrectnessで正確性を数値化。
4. `langchain` + `langsmith`: 取得/評価はLangChain経由で実装、評価ログはLangSmithに集約。
5. `trulens`: フィードバック関数で「正確性/整合性」を定義し、評価ログと改善の効果を追跡。

### 人間による改善運用
- Judgeスコアと理由をJSONで保存し、人が低スコア項目の原因を確認。
- プロンプトや検索指示（例: 日本語優先、公式サイト優先）を改善し、再度ループ実行。

## まとめ（用途別の推奨）
1. **最短で実装**: `google-genai`
2. **GCP運用 + 自律フロー重視**: `google-adk`
3. **参照データ比較を重視**: `ragas`
4. **評価の可視化/回帰検知重視**: `langsmith`
5. **評価指標の拡張性重視**: `trulens`

---

## 学習コストと導入メモ（目安）

**学習コスト（低→高）**:
`google-genai` → `ragas` → `trulens` → `langchain` + `langsmith` → `google-adk`

**導入メモ**:
- `google-genai`: SDK単体で開始でき、最小構成に向く。
- `ragas`: 参照データの準備が前提。評価対象の整形が必要。
- `trulens`: 評価設計（フィードバック関数）の作り込みが必要。
- `langchain` + `langsmith`: 概念理解と設定項目が多め。
- `google-adk`: エージェント設計が必要で、学習コストが高い分ループ運用に強い。

---

## このリポジトリ向けの推奨導入順（実装優先）

1. `google-genai` で Direct Assessment を先に作る
2. 同じ評価プロンプトを使って Self-Refinement Loop を追加する
3. 必要になったら `ragas` で参照データ比較を導入する
4. 運用フェーズで `langsmith` または `trulens` を追加する
5. 複数ツール連携が必要になった段階で `google-adk` に拡張する

理由:
- 現在の構成（`app/main.py` 中心）と最も整合するのが `google-genai`。
- 先に評価ロジックを固定すると、後からフレームワークを差し替えやすい。
- 可観測性ツールはPoC段階では過剰になりやすく、運用移行時の追加が合理的。

## PoCで先に決める仕様（最小）

### 評価対象フィールド
- `title`
- `year`
- `director`
- `cast`
- `genre`

### Judge出力JSON（例）
```json
{
  "movie_id": "tt0133093",
  "scores": {
    "title": 1.0,
    "year": 0.6,
    "director": 1.0,
    "cast": 0.7,
    "genre": 0.8
  },
  "overall_score": 0.82,
  "needs_retry_fields": ["year", "cast"],
  "reasons": {
    "year": "公開年が複数候補で曖昧",
    "cast": "主要キャストの欠落がある"
  }
}
```

### 反復停止条件
- `overall_score >= 0.90` で停止
- もしくは `max_iterations = 3` で停止
- 同一フィールドが2回連続で改善しない場合は打ち切り

## 運用で見るKPI（最小セット）

1. 1件あたり平均 `overall_score`
2. 再取得が必要だった件数の割合（retry rate）
3. 反復1回あたりの改善量（delta score）
4. 1件あたりの推定コスト（APIコール数ベース）
5. 人手レビューでの最終正答率（サンプリング）

## 将来拡張の判断基準

- `ragas` を入れるタイミング:
  参照データ（正解JSON）が十分に整備され、定量比較を厳密化したいとき。
- `langsmith` / `trulens` を入れるタイミング:
  バージョン差分比較、回帰検知、ダッシュボード運用が必要になったとき。
- `google-adk` を入れるタイミング:
  検索・検証・再取得をエージェントで分業し、ルールベース以上の自律判断が必要になったとき。

## ここまでの結論

- 学習兼PoC段階では `google-genai` 単体が最短。
- 参照データが整ってきたら `ragas` が強い。
- 運用監視を強化する段階で `langsmith` または `trulens` を追加する。
- 多段ツール連携の自律化が要件化したら `google-adk` に進む。

---

## 先行フェーズ（まず実装方法を把握する）

直近で着手する前提として、まずは「実装の見取り図」を短時間で固める。

### 目標（30〜90分）
- どのライブラリで最初に作るかを確定する
- 入出力JSONの形を固定する
- 実装の最小手順を1ページで説明できる状態にする

### 最初に確定すること
1. 初期採用ライブラリ: `google-genai`
2. 評価方式: Direct Assessment（項目別スコア + 理由）
3. 再取得条件: `overall_score < 0.90` または必須項目スコア不足
4. 停止条件: 最大3反復
5. 保存先: `app/data/output/` 配下に評価JSONを保存

### 実装把握のチェックリスト（開始前）
- `app/main.py` の現行入出力を確認した
- Judge用の入力項目（title/release_date/country/cast など）を確認した
- Judge出力JSONの必須キー（scores/overall_score/reasons）を決めた
- 閾値（0.90）と再試行上限（3回）を決めた
- 失敗時ログ（API失敗、JSON不正）をどこに残すか決めた

### 実装把握フェーズの完了条件
- 「1件の映画データを評価してJSON保存する」までの流れを説明できる
- 再取得ループに入る判定条件を説明できる
- 次に作るファイル候補を列挙できる

### 次に作るファイル候補（最小）
- `app/movie_metadata/judge_models.py`
- `app/movie_metadata/judge_prompts.py`
- `app/movie_metadata/direct_assessment.py`
- `app/movie_metadata/judge_json_writer.py`

### `app/main.py` 入出力確認メモ（現行）
- 入力CSV: `app/data/movies_test3.csv`
- 入力必須列: `title`, `release_date`, `country`
- 取得処理: `fetch_movie_metadata(movie, api_key)` を映画ごとに実行
- 出力JSON: `app/data/output/movie_metadata_YYYYMMDD_HHMMSS.json`
- 出力形式: `MovieMetadata` の配列をJSONで保存

### `MovieMetadata` の現行フィールド
- `title`
- `japanese_titles`
- `release_date`
- `country`
- `distributor`
- `box_office`
- `cast`
- `music`
- `voice_actors`

### Judge導入時の注意（現行構成に合わせる）
- Judge対象はまず `MovieMetadata` の現行9項目を前提にする
- 先行評価対象（最小）は `title/release_date/country/cast` から開始してもよい
- `metadata_fetcher.py` は取得失敗時にデフォルト値を返すため、Judge側で
  `情報なし` の扱いルールを事前に決める

### Judge実行時の推奨モデル
- 推奨: `gemini-3-flash-preview`（`metadata_fetcher.py` と同じモデルを使用）
- 理由: `google_search` ツールと構造化出力（`response_schema`）の組み合わせで
  モデル差による `400 INVALID_ARGUMENT` を避けやすい
- 運用ルール: 取得側とJudge側でモデルをそろえ、片側だけ変更しない
