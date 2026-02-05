# LLM as a Judge 実装計画

## プロジェクト概要

Google Generative AI (google-genai) SDKを使用して、LLM as a Judgeの学習用サンプルコードを作成します。

---

## LLM as a Judge とは (学習用まとめ)

### 基本概念

LLM as a Judgeは、大規模言語モデルに「評価者」の役割を与え、AIや人間の回答品質を自動評価する手法です。

**主な利点**:
- 人手レビューの500〜5000倍のコスト効率
- 人間との一致率 最大85% (人間同士81%を上回る)
- 従来指標(BLEU/ROUGE)では測れない「一貫性」「有用性」「事実正確性」を評価

### 3つの評価パターン

#### 1. Direct Assessment (Point-wise)
1つの回答を複数観点で評価し、スコアと理由を出力

**用途**: 個別回答の品質測定、改善点の特定

#### 2. Pairwise Comparison
2つの回答を比較して優劣を判定

**用途**: A/Bテスト、モデル比較、ランキング

**重要**: Position bias(提示順序による偏り)対策が必須
- 解決策: A-B と B-A の両方向で評価し、一貫性を確認

#### 3. Self-Refinement Loop
評価→改善→再評価のイテレーションで品質を段階的に向上

**用途**: 実際の品質管理、自動改善システム

**フロー**:
```
1. 初回生成
2. Judge評価 (スコア + フィードバック)
3. 閾値判定
   - 閾値以上 → 完了
   - 閾値未満 → フィードバックを元に再生成 (ステップ2へ)
4. 最大試行回数到達で終了
```

### 注意すべきバイアス

| バイアス | 説明 | 対策 |
|---------|------|------|
| Position bias | 最初/最後の選択肢を優遇(GPT-4で40%不一致) | 両方向評価 + 一貫性チェック |
| Verbosity bias | 長い回答を優遇(約15%水増し) | 1-4スケール、簡潔さを明示評価 |

---

---

## 調査結果

### 既存コードベースの構造

**既存の実装パターン** (`/workspaces/learn-google-genai/app/movie_metadata/metadata_fetcher.py:35`)
```python
client = genai.Client(api_key=api_key)  # Gemini Developer API
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=MovieMetadata,  # Pydantic schema
    ),
)
```

**主な特徴**:
- Pydanticモデルで構造化出力
- モジュール分割設計 (models, fetcher, reader, writer)
- API key認証のみ(GCPプロジェクト不要)

### 実装アプローチの選択肢

#### **アプローチA: Vertex AI 評価サービス (公式)**

**概要**: Google Cloud の公式評価API ([公式ドキュメント](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview))

```python
from vertexai import Client  # 注意: genai.Clientとは別物

client = Client(project=PROJECT_ID, location=LOCATION)
eval_result = client.evals.evaluate(
    dataset=eval_dataset,
    metrics=[types.RubricMetric.GENERAL_QUALITY]
)
```

**利点**:
- 公式の評価機能
- Adaptive Rubrics (動的評価基準生成)
- メトリクスが豊富

**欠点**:
- GCPプロジェクトが必要
- 既存コード(API key認証)と異なる認証方式
- 学習用としては「ブラックボックス」化

---

#### **アプローチB: Gemini Developer API で手動実装 (推奨)**

**概要**: 既存の `genai.Client(api_key=...)` を使い、Judge評価ロジックを自分で実装

```python
# 既存パターンを活用
client = genai.Client(api_key=api_key)

# Judge用のPydanticスキーマを定義
class JudgeEvaluation(BaseModel):
    score: int = Field(description="1-5のスコア")
    reasoning: str = Field(description="評価理由")

# Judgeとして評価
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=judge_prompt,  # 評価基準を含むプロンプト
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=JudgeEvaluation,
    ),
)
```

**利点**:
- 既存環境をそのまま使える (API keyのみ)
- LLM as a Judgeの仕組みを理解できる
- シンプルで学習に最適
- モジュール設計パターンを再利用可能

**欠点**:
- 評価ロジックを自分で実装する必要がある
- Vertex AI評価サービスほど高機能ではない

---

## 実装パターン候補 (アプローチB採用時)

### パターン1: Direct Assessment (Point-wise) ⭐推奨
**最もシンプルで学習に最適**

```
入力: AIの回答
Judge: 評価基準に基づきスコアリング
出力: スコア + 理由
```

**実装内容**:
- 1つの回答を評価
- 複数の観点 (正確性、明瞭性、簡潔性など) でスコアリング
- 評価理由を自然言語で出力

---

### パターン2: Pairwise Comparison
**より実践的**

```
入力: 回答A + 回答B
Judge: どちらが優れているか判定
出力: 勝者 + 理由
```

**実装内容**:
- 2つの回答を比較
- Position bias対策(A-B, B-Aの両方評価)
- 実用的なA/Bテストシナリオ

---

### パターン3: Self-Refinement Loop
**最も高度**

```
1. 初回生成 → Judge評価
2. スコアが閾値未満 → フィードバックを元に再生成
3. 再評価
4. 閾値以上 → 最終出力
```

**実装内容**:
- 評価→改善のイテレーション
- 品質向上プロセスの可視化
- 実践的な品質管理パターン

---

## 調査項目チェックリスト

- [x] 既存コードベースの構造確認
- [x] google-genai SDKの使用パターン確認
- [x] 実装アプローチの選択肢整理
- [x] ユーザーの選択確認
  - [x] **選択**: Gemini Developer API で手動実装
  - [x] **選択**: 全パターン実装 (Direct → Pairwise → Self-Refinement)
- [x] サンプルコードの詳細設計

---

## 最終実装計画

### ディレクトリ構造

```
app/
├── llm_judge/                      # 新規モジュール
│   ├── __init__.py                # パッケージエクスポート
│   ├── models.py                  # Pydanticモデル定義
│   ├── prompts.py                 # システムプロンプト定義
│   ├── judge_client.py            # LLM Judge呼び出し基底クラス
│   ├── direct_assessment.py       # Pattern 1
│   ├── pairwise_comparison.py     # Pattern 2
│   ├── self_refinement.py         # Pattern 3
│   └── sample_data.py             # テストデータ
├── data/
│   └── llm_judge/
│       ├── input/                 # 入力データ
│       └── output/                # 評価結果
└── main_judge.py                  # デモ実行スクリプト
```

### 実装ステップ (段階的に実装)

#### **Phase 1: 基盤構築** (優先度: 高)

1. **models.py** - 全Pydanticモデル定義
   - `Question`, `Answer` (共通)
   - `AspectScore`, `DirectAssessmentResult` (Direct Assessment)
   - `PairwiseComparisonResult`, `PairwiseAggregatedResult` (Pairwise)
   - `RefinementIteration`, `SelfRefinementResult` (Self-Refinement)

2. **prompts.py** - システムプロンプトとテンプレート
   - Direct Assessment用プロンプト
   - Pairwise Comparison用プロンプト
   - Self-Refinement用プロンプト (Generator + Evaluator)

3. **sample_data.py** - テストデータ
   - サンプル質問 (Python, 機械学習, 比較分析)
   - 品質レベル別の回答 (poor/medium/good/excellent)

4. **__init__.py** - モジュールエクスポート

#### **Phase 2: Pattern 1 - Direct Assessment** (優先度: 高)

1. **direct_assessment.py** の実装
   - `assess_answer()` 関数
   - 複数観点での評価 (正確性、明瞭性、簡潔性、完全性、実用性)
   - スコア 1-5 + 評価理由
   - 既存の `genai.Client(api_key=...)` パターンを活用

2. **main_judge.py** にデモコード追加
   - Direct Assessment実行例
   - サンプルデータでの動作確認

#### **Phase 3: Pattern 2 - Pairwise Comparison** (優先度: 中)

1. **pairwise_comparison.py** の実装
   - `compare_pair()` - 1回の比較
   - `compare_with_position_bias_check()` - A-B, B-A両方評価
   - 一貫性チェックロジック
   - Position bias対策

2. **main_judge.py** にデモコード追加

#### **Phase 4: Pattern 3 - Self-Refinement** (優先度: 中)

1. **self_refinement.py** の実装
   - `generate_answer()` - 回答生成
   - `evaluate_answer()` - 評価 (Direct Assessmentベース)
   - `refine_with_feedback()` - ループ制御
     - 閾値チェック
     - 最大イテレーション制限
     - 改善提案の生成とフィードバック

2. **main_judge.py** にデモコード追加

#### **Phase 5: 統合とドキュメント** (優先度: 低)

1. 全パターンの統合テスト
2. README作成
3. エラーハンドリング強化

### 依存関係

```
Phase 1 (基盤)
    ↓
Phase 2 (Direct Assessment) ← 最も基本的
    ↓
Phase 3 (Pairwise) ← Phase 1に依存
    ↓
Phase 4 (Self-Refinement) ← Phase 2の評価ロジックを再利用
    ↓
Phase 5 (統合)
```

---

## 主要モデル設計

### Direct Assessment

```python
class AspectScore(BaseModel):
    aspect: str  # 評価観点名
    score: int  # 1-5のスコア
    reasoning: str  # 評価理由

class DirectAssessmentResult(BaseModel):
    answer_id: str
    question_text: str
    answer_text: str
    aspect_scores: list[AspectScore]  # 複数観点
    overall_score: float  # 総合スコア(平均値)
    overall_reasoning: str
```

### Pairwise Comparison

```python
class PairwiseComparisonResult(BaseModel):
    winner: str  # 'A', 'B', 'TIE'
    reasoning: str
    confidence: str  # 'high', 'medium', 'low'

class PairwiseAggregatedResult(BaseModel):
    comparison_ab: PairwiseComparisonResult  # A vs B
    comparison_ba: PairwiseComparisonResult  # B vs A (Position bias対策)
    final_winner: str  # 'A', 'B', 'TIE', 'INCONSISTENT'
    consistency_note: str
```

### Self-Refinement

```python
class RefinementIteration(BaseModel):
    iteration: int
    generated_answer: str
    evaluation_score: float
    evaluation_reasoning: str
    meets_threshold: bool
    improvement_suggestions: str | None

class SelfRefinementResult(BaseModel):
    iterations: list[RefinementIteration]  # 全履歴
    final_answer: str
    final_score: float
    success: bool  # 閾値到達 or 最大試行到達
```

---

## 技術的ポイント

### 既存パターンの再利用

既存の `/workspaces/learn-google-genai/app/movie_metadata/metadata_fetcher.py:35` パターンを踏襲:

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-3-flash-preview",  # 既存と同じモデル
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=DirectAssessmentResult,  # Pydanticモデル
    ),
)

# Pydanticでパース
result = DirectAssessmentResult.model_validate_json(response.text)
```

### エラーハンドリング

既存コードと同様のtry-exceptパターン:

```python
try:
    response = client.models.generate_content(...)
    if response.text is None:
        raise ValueError("API応答が空です")
    result = Model.model_validate_json(response.text)
    return result
except Exception as e:
    print(f"警告: 評価に失敗しました ({type(e).__name__}: {e})")
    # フォールバック処理
```

---

## 検証方法

### 実装後の動作確認

1. **Phase 2完了時**: Direct Assessment実行
   ```bash
   cd app
   uv run main_judge.py --pattern direct
   ```
   - サンプル質問・回答で評価実施
   - スコアと理由が出力されることを確認

2. **Phase 3完了時**: Pairwise Comparison実行
   ```bash
   uv run main_judge.py --pattern pairwise
   ```
   - 2つの回答を比較
   - Position bias対策が機能することを確認

3. **Phase 4完了時**: Self-Refinement実行
   ```bash
   uv run main_judge.py --pattern refinement
   ```
   - イテレーションループが動作することを確認
   - 評価→改善のサイクルを観察

4. **Phase 5完了時**: 全パターン統合実行
   ```bash
   uv run main_judge.py --pattern all
   ```

### 品質チェック

各Phaseの実装後:
```bash
cd app
uv run ruff format . && uv run ruff check --fix . && uv run ty check
```

---

## クリティカルファイル

実装時に重要となるファイル:

- `/workspaces/learn-google-genai/app/llm_judge/models.py` - 全Pydanticモデル
- `/workspaces/learn-google-genai/app/llm_judge/prompts.py` - 評価プロンプト
- `/workspaces/learn-google-genai/app/llm_judge/direct_assessment.py` - Pattern 1実装
- `/workspaces/learn-google-genai/app/llm_judge/self_refinement.py` - Pattern 3実装(最も複雑)
- `/workspaces/learn-google-genai/app/movie_metadata/metadata_fetcher.py` - 参考実装パターン
