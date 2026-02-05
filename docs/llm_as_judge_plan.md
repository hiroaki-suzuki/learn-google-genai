# LLM as a Judge 学習ノート（段階学習・実装計画・全文）

## 目的
LLM as a Judgeの基本概念を理解し、Direct Assessmentを中心に実装の流れを読解できる状態にする。

## プロジェクト概要
Google Generative AI (google-genai) SDKを使用して、LLM as a Judgeの学習用サンプルコードを作成する。

---

## 進捗管理（チェックリスト）

- [ ] Step 0: 学習の進め方を理解する
- [ ] Step 1: LLM as a Judgeの概念を把握する
- [ ] Step 2: 3つの評価パターンを理解する
- [ ] Step 3: バイアスと対策を理解する
- [ ] Step 4: 実装アプローチを選択・把握する
- [ ] Step 5: Direct Assessment を実装する
- [ ] Step 6: Pairwise Comparison を実装する
- [ ] Step 7: Self-Refinement Loop を実装する
- [ ] Step 8: 統合・検証・品質チェック

**現在の進捗**: 未着手

**次回開始点のルール**:
- 未着手の場合はStep 0から開始
- 途中の場合は「最後に完了したStepの次」から開始
- 完了済みは復習フェーズへ

---

## Step 0: 学習の進め方を理解する

**学習ゴール**:
- 1回の学習で「読む範囲」と「アウトプット」が分かる状態になる。

**読む範囲**:
- 「読むサポート運用ルール（質問テンプレ）」を流し読み。

**小さなアウトプット**:
- 「テンプレC: 1行まとめ」を使って本日の目標を1行で書く。

---

## Step 1: LLM as a Judge とは（入門）

**要点**
- LLM as a Judgeは、LLMに「評価者」の役割を与え、回答品質を自動評価する考え方。
- 従来指標（BLEU/ROUGE）では拾いにくい「一貫性」「有用性」「事実正確性」を評価しやすい。
- 人手より低コストになり得るが、条件依存であり万能ではない。

**かみ砕き**
- 人が採点する代わりに、別のAIが採点役になるイメージ。

**例え**
- 先生の代わりに「採点係のAI」を置いて、同じ基準で大量の答案を採点する感じ。

**注意点**
- 評価は便利だが、AIにも癖や偏りがあるため設計が重要。

**まとめ**
- 速く安く評価できるが、バイアス対策と基準設計が必須。

**読むフェーズ**: 入門

**参考リンク**:
- 一次資料（英語）
```text
https://arxiv.org/abs/2306.05685
```
- 概要理解（日本語）
```text
https://edx.nii.ac.jp/lecture/20250418-04
```

**読み方ガイド**:
- 日本語講演概要の最初の段落だけで十分。
- 論文はAbstractの冒頭だけ読む。

**読後サポート**:
- わからない用語を3つまで箇条書きで送ってください。言い換えと要点整理をします。

**小さなアウトプット**:
- 「LLM as a Judgeを一言で言うと？」を1行で書く。

---

## Step 2: 3つの評価パターン（理解）

### 2-1. Direct Assessment

**要点**
- 1つの回答を複数観点で評価し、スコアと理由を出す。

**かみ砕き**
- 1つの答案を「正確さ」「わかりやすさ」などで採点する方法。

**例え**
- 5教科の成績表のように、観点ごとの点数をつける。

**注意点**
- どの観点を選ぶかで評価の性格が変わる。

**まとめ**
- 最も基本で学習に向いている。

**読むフェーズ**: 理解

**参考リンク**:
- 一次資料（英語）
```text
https://arxiv.org/abs/2306.05685
```
- 概要理解（日本語）
```text
https://www.issoh.co.jp/tech/details/8712/
```

**読み方ガイド**:
- 日本語記事は「LLM-as-a-Judgeとは」節だけ読む。
- 論文は「LLM-as-a-judgeを使う理由」の段落だけ確認する。

**読後サポート**:
- Direct Assessmentの「評価観点」を自分の言葉で1行書いてください。添削します。

### 2-2. Pairwise Comparison

**要点**
- 2つの回答を比較して優劣を決める。

**かみ砕き**
- AとBを並べて「どっちが良いか」を判定する方式。

**例え**
- 2つの作文を読み比べて、良い方に票を入れる。

**注意点**
- 順序で印象が変わるため、A-BとB-Aの両方評価が有効。

**まとめ**
- A/Bテストに向いている。

**読むフェーズ**: 理解

**参考リンク**:
- 一次資料（英語）
```text
https://arxiv.org/abs/2403.04132
```
- 概要理解（日本語）
```text
https://llm-jp.nii.ac.jp/ja/blog/blog-836/
```

**読み方ガイド**:
- 日本語記事は「経緯」「概要」だけ読む。数式は読み飛ばして問題なし。
- 論文はAbstractの「pairwise comparison」の部分だけ読む。

**読後サポート**:
- 「なぜ順序を入れ替えるのか」を一言で送ってください。補足します。

### 2-3. Self-Refinement Loop

**要点**
- 評価→改善→再評価を繰り返して品質を上げる。

**かみ砕き**
- 添削と書き直しを繰り返して文章を良くする方法。

**例え**
- 作文を先生に直してもらい、また書き直す。

**注意点**
- 回数を増やすと時間とコストが増える。

**まとめ**
- 実務の品質改善に向くが、最も高度。

**読むフェーズ**: 理解

**参考リンク**:
- 一次資料（英語）
```text
https://arxiv.org/abs/2303.17651
```
- 概要理解（日本語）
```text
https://www.itmedia.co.jp/news/articles/2304/18/news033.html
```

**読み方ガイド**:
- 日本語記事は冒頭の要約と図だけ読む。
- 論文はAbstractの「iteration / feedback」部分だけ読む。

**読後サポート**:
- 「改善ループの良い点・不安点」を1つずつ書いて送ってください。整理します。

**小さなアウトプット**:
- 「自分の用途に合いそうなパターンはどれか」を1行で書く。

---

## Step 3: 注意すべきバイアス（理解）

**要点**
- Position bias: 最初や最後の回答を優遇しやすい。
- Verbosity bias: 長い回答を優遇しやすい。

**かみ砕き**
- 順番や長さに引っ張られる「評価のクセ」。

**例え**
- テストの採点で、最初に読んだ答案が印象に残る。

**注意点**
- 対策として順序を入れ替える、簡潔さを評価基準に入れる。

**まとめ**
- バイアス対策をしないと評価が歪む。

**読むフェーズ**: 理解

**参考リンク**:
- 一次資料（英語）
```text
https://arxiv.org/abs/2306.05685
```
- 概要理解（日本語）
```text
https://www.issoh.co.jp/tech/details/10331/
```

**読み方ガイド**:
- 日本語記事は「バイアス」「対策」の見出しだけ読む。
- 論文は「bias」や「position/verbosity」の段落だけ拾い読み。

**読後サポート**:
- 「どのバイアスが気になるか」を1行で教えてください。対策の具体例を一緒に整理します。

**小さなアウトプット**:
- 「自分ならどう対策するか」を1行で書く。

---

## Step 4: 実装アプローチを選択・把握する

### アプローチB（主軸）: Gemini Developer APIで手動実装

**要点**
- 既存の `genai.Client(api_key=...)` を使い、Judge評価を自分で組む。

**かみ砕き**
- 自分で採点基準を作り、AIに採点させる方式。

**注意点**
- 評価ロジックの設計が必要。

**まとめ**
- 学習に最適で仕組み理解に向く。

**読むフェーズ**: 実装

**参考リンク**:
- 一次資料（公式）
```text
https://ai.google.dev/gemini-api/docs/structured-output
```
- 概要理解（公式ブログ）
```text
https://blog.google/technology/developers/gemini-api-structured-outputs/
```

**読み方ガイド**:
- 公式ドキュメントは「Generating JSON」節の最初だけ読む。
- ブログは「Structured Outputsとは何か」の説明だけ拾い読み。

**読後サポート**:
- 「JSONスキーマって何？」の一言質問でもOKです。図解的に説明します。

### アプローチA（補足）: Vertex AI 評価サービス

**要点**
- Google Cloudの公式評価APIを使う方式。

**かみ砕き**
- 公式の採点サービスを使うイメージ。

**注意点**
- GCPプロジェクトが必要。
- API keyだけで動かす既存コードとは違う。

**まとめ**
- 高機能だが学習用にはやや重い。

**読むフェーズ**: 実装

**参考リンク**:
- 一次資料（公式）
```text
https://cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview
```
- 概要理解（公式ノートブック）
```text
https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/evaluation/quick_start_gen_ai_eval.ipynb
```

**読み方ガイド**:
- 公式概要は「Use cases」だけ読む。
- ノートブックは冒頭の説明文だけ読む（コードは後回し）。

**読後サポート**:
- Vertex AIの用語が難しければ、どの単語が引っかかったか教えてください。

**小さなアウトプット**:
- 「なぜGemini Dev APIを主軸にするか」を1行で書く。

---

## Step 5: Direct Assessment を実装する

**実装パターン候補**:
- Direct Assessment → Pairwise → Self-Refinement の順で実装する。

**ディレクトリ構造（予定）**

```
app/
├── llm_judge/
│   ├── __init__.py
│   ├── models.py
│   ├── prompts.py
│   ├── judge_client.py
│   ├── direct_assessment.py
│   ├── pairwise_comparison.py
│   ├── self_refinement.py
│   └── sample_data.py
├── data/
│   └── llm_judge/
│       ├── input/
│       └── output/
└── main_judge.py
```

**主要モデル設計（参考）**

**Direct Assessment**
```python
class AspectScore(BaseModel):
    aspect: str
    score: int
    reasoning: str

class DirectAssessmentResult(BaseModel):
    answer_id: str
    question_text: str
    answer_text: str
    aspect_scores: list[AspectScore]
    overall_score: float
    overall_reasoning: str
```

---

## Step 6: Pairwise Comparison を実装する

**主要モデル設計（参考）**

**Pairwise Comparison**
```python
class PairwiseComparisonResult(BaseModel):
    winner: str
    reasoning: str
    confidence: str

class PairwiseAggregatedResult(BaseModel):
    comparison_ab: PairwiseComparisonResult
    comparison_ba: PairwiseComparisonResult
    final_winner: str
    consistency_note: str
```

---

## Step 7: Self-Refinement Loop を実装する

**主要モデル設計（参考）**

**Self-Refinement**
```python
class RefinementIteration(BaseModel):
    iteration: int
    generated_answer: str
    evaluation_score: float
    evaluation_reasoning: str
    meets_threshold: bool
    improvement_suggestions: str | None

class SelfRefinementResult(BaseModel):
    iterations: list[RefinementIteration]
    final_answer: str
    final_score: float
    success: bool
```

---

## Step 8: 統合・検証・品質チェック

**検証方法**

1. Direct Assessment実行
```bash
cd app
uv run main_judge.py --pattern direct
```

2. Pairwise Comparison実行
```bash
cd app
uv run main_judge.py --pattern pairwise
```

3. Self-Refinement実行
```bash
cd app
uv run main_judge.py --pattern refinement
```

4. 全パターン統合実行
```bash
cd app
uv run main_judge.py --pattern all
```

**品質チェック**

```bash
cd app
uv run ruff format . && uv run ruff check --fix . && uv run ty check
```

---

## 読むサポート運用ルール（質問テンプレ）

### 使い方の流れ（1分）
1. まず「読むフェーズ」と「読み方ガイド」だけ確認する。
2. 参考リンクは1本だけ読む（時間があれば2本目）。
3. 読後サポートのテンプレに沿って、短く質問を書く。

### テンプレ（短文でOK）

**テンプレA: 用語がわからない**
- 用語:
- どこで出てきたか:
- 自分の理解（あれば）:

**テンプレB: ここが難しい**
- 文章の場所（見出し名でOK）:
- 何がわからないか:
- 自分の例え（あれば）:

**テンプレC: 1行まとめ**
- 1行まとめ:
- 自信度（高/中/低）:

**テンプレD: 進め方の相談**
- 今のフェーズ:
- つまずきポイント:
- 望む説明（例え/具体例/図解）:

### 返答の方針（こちらの対応）
- 用語は「正確な定義 → やさしい言い換え → 例え」の順で説明する。
- 数式は使わず、図解的な説明を優先する。
- 長い説明は「要点3つ」でまとめる。

---

## 参考文献（主要根拠）

**読む順序のおすすめ**
1. Gemini API Structured Output
2. MT-Bench

**MT-Bench: LLM-as-a-judge の基礎的検証論文**
```text
https://arxiv.org/abs/2306.05685
```

**Gemini API Structured Output: JSON出力とPydanticスキーマの公式ガイド**
```text
https://ai.google.dev/gemini-api/docs/structured-output
```
