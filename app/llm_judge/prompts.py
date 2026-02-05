"""LLM as a Judge用のプロンプトテンプレート"""

# ========================================
# Direct Assessment用プロンプト
# ========================================

DIRECT_ASSESSMENT_PROMPT_TEMPLATE = """
# 役割: AI回答評価者

あなたは、AI生成回答の品質を客観的に評価する専門家です。

## 質問
{question}

## 評価対象の回答
{answer}

## 評価観点と基準

以下の5つの観点について、それぞれ1-5のスコアで評価してください。

### 1. 正確性 (Accuracy)
- **5点**: 完全に正確で、事実誤認が一切ない
- **4点**: ほぼ正確だが、軽微な不正確さがある
- **3点**: 部分的に正確だが、重要な誤りがある
- **2点**: 多くの誤りがあり、誤解を招く
- **1点**: 完全に不正確、またはナンセンス

### 2. 明瞭性 (Clarity)
- **5点**: 非常に明確で理解しやすい
- **4点**: ほぼ明確だが、一部わかりにくい箇所がある
- **3点**: ある程度理解できるが、曖昧な表現が多い
- **2点**: 理解しにくく、混乱を招く
- **1点**: 意味不明

### 3. 簡潔性 (Conciseness)
- **5点**: 必要十分な情報を簡潔に提供
- **4点**: ほぼ簡潔だが、やや冗長な部分がある
- **3点**: 中程度の冗長性がある
- **2点**: 不必要な情報が多く、要点が埋もれている
- **1点**: 極度に冗長、または情報不足

### 4. 完全性 (Completeness)
- **5点**: 質問に対して完全に答えている
- **4点**: ほぼ完全だが、軽微な情報不足がある
- **3点**: 重要な情報が一部欠けている
- **2点**: 多くの重要情報が欠けている
- **1点**: 質問に答えていない

### 5. 実用性 (Usefulness)
- **5点**: 非常に実用的で、すぐに活用できる
- **4点**: 実用的だが、一部追加情報が必要
- **3点**: ある程度実用的だが、限定的
- **2点**: あまり実用的でない
- **1点**: 全く実用的でない

## 出力形式

各観点のスコアと理由、および総合評価を提供してください。
"""

# ========================================
# Pairwise Comparison用プロンプト
# ========================================

PAIRWISE_COMPARISON_PROMPT_TEMPLATE = """
# 役割: AI回答比較評価者

あなたは、2つのAI生成回答を比較し、どちらが優れているかを客観的に判定する専門家です。

## 質問
{question}

## 回答A
{answer_a}

## 回答B
{answer_b}

## 評価基準

以下の観点で2つの回答を比較してください。

1. **正確性**: どちらがより正確か
2. **明瞭性**: どちらがより理解しやすいか
3. **完全性**: どちらがより完全に質問に答えているか
4. **実用性**: どちらがより実用的か

## 判定ルール

- **A**: 回答Aが明らかに優れている
- **B**: 回答Bが明らかに優れている
- **TIE**: 両者が同等の品質

## 信頼度

- **high**: 明確な差があり、判定に自信がある
- **medium**: ある程度の差があるが、判断が難しい部分もある
- **low**: 差が非常に小さく、判定が困難

## 出力形式

勝者(A/B/TIE)、判定理由、および信頼度を提供してください。
"""

# ========================================
# Self-Refinement用プロンプト
# ========================================

REFINEMENT_GENERATOR_PROMPT_TEMPLATE = """
# 役割: AI回答生成者

以下の質問に対して、詳細で正確な回答を生成してください。

## 質問
{question}

## 前回のフィードバック(ある場合)
{feedback}

## 指示

{feedback_instruction}
"""

REFINEMENT_EVALUATOR_PROMPT_TEMPLATE = """
# 役割: AI回答評価者

あなたは、AI生成回答の品質を客観的に評価し、改善提案を行う専門家です。

## 質問
{question}

## 評価対象の回答
{answer}

## 評価基準

以下の観点で回答を評価し、1-5のスコア(小数点可)を算出してください。

- **正確性**: 事実誤認がないか
- **明瞭性**: 理解しやすいか
- **完全性**: 質問に完全に答えているか
- **実用性**: 実際に役立つか

## 閾値: {threshold}

スコアが閾値以上の場合は「合格」、未満の場合は「改善が必要」と判定してください。

## 出力形式

1. **評価スコア** (1.0-5.0の範囲)
2. **評価理由** (なぜそのスコアなのか)
3. **改善提案** (閾値未達の場合は具体的な改善点、閾値以上の場合は「なし」)
"""


def build_direct_assessment_prompt(question: str, answer: str) -> str:
    """Direct Assessment用プロンプトを構築"""
    return DIRECT_ASSESSMENT_PROMPT_TEMPLATE.format(question=question, answer=answer)


def build_pairwise_comparison_prompt(
    question: str, answer_a: str, answer_b: str
) -> str:
    """Pairwise Comparison用プロンプトを構築"""
    return PAIRWISE_COMPARISON_PROMPT_TEMPLATE.format(
        question=question, answer_a=answer_a, answer_b=answer_b
    )


def build_refinement_generator_prompt(
    question: str, feedback: str | None = None
) -> str:
    """Self-Refinement Generator用プロンプトを構築"""
    if feedback:
        feedback_text = feedback
        feedback_instruction = "前回のフィードバックを参考に、回答を改善してください。"
    else:
        feedback_text = "なし(初回生成)"
        feedback_instruction = "質問に対して、最善の回答を生成してください。"

    return REFINEMENT_GENERATOR_PROMPT_TEMPLATE.format(
        question=question,
        feedback=feedback_text,
        feedback_instruction=feedback_instruction,
    )


def build_refinement_evaluator_prompt(
    question: str, answer: str, threshold: float
) -> str:
    """Self-Refinement Evaluator用プロンプトを構築"""
    return REFINEMENT_EVALUATOR_PROMPT_TEMPLATE.format(
        question=question, answer=answer, threshold=threshold
    )
