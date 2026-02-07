"""LLM as a Judge用のPydanticモデル定義"""

from pydantic import BaseModel, Field

# ========================================
# 共通モデル
# ========================================


class Question(BaseModel):
    """評価対象の質問"""

    question_id: str = Field(description="質問の一意ID")
    text: str = Field(description="質問文")
    category: str = Field(description="質問のカテゴリー")


class Answer(BaseModel):
    """評価対象の回答"""

    answer_id: str = Field(description="回答の一意ID")
    text: str = Field(description="回答文")


# ========================================
# Direct Assessment用モデル
# ========================================


class AspectScore(BaseModel):
    """個別観点の評価スコア"""

    aspect: str = Field(description="評価観点名")
    score: int = Field(description="1-5のスコア", ge=1, le=5)
    reasoning: str = Field(description="このスコアをつけた理由")


class DirectAssessmentResult(BaseModel):
    """Direct Assessment評価結果"""

    answer_id: str = Field(description="評価対象の回答ID")
    question_text: str = Field(description="質問文")
    answer_text: str = Field(description="回答文")
    aspect_scores: list[AspectScore] = Field(description="各観点のスコア")
    overall_score: float = Field(description="総合スコア(平均値)", ge=1.0, le=5.0)
    overall_reasoning: str = Field(description="総合評価の理由")


# ========================================
# Pairwise Comparison用モデル
# ========================================


class PairwiseComparisonResult(BaseModel):
    """Pairwise Comparison評価結果"""

    winner: str = Field(description="勝者 ('A', 'B', 'TIE')")
    reasoning: str = Field(description="この判定をした理由")
    confidence: str = Field(description="判定の信頼度 ('high', 'medium', 'low')")


class PairwiseAggregatedResult(BaseModel):
    """Position bias対策後の集約結果"""

    comparison_ab: PairwiseComparisonResult = Field(description="A vs B の比較結果")
    comparison_ba: PairwiseComparisonResult = Field(description="B vs A の比較結果")
    final_winner: str = Field(
        description="最終的な勝者 ('A', 'B', 'TIE', 'INCONSISTENT')"
    )
    consistency_note: str = Field(description="一貫性に関する説明")


# ========================================
# Self-Refinement用モデル
# ========================================


class RefinementIteration(BaseModel):
    """Self-Refinementの1イテレーション"""

    iteration: int = Field(description="イテレーション番号(1から開始)")
    generated_answer: str = Field(description="生成された回答")
    evaluation_score: float = Field(description="評価スコア", ge=1.0, le=5.0)
    evaluation_reasoning: str = Field(description="評価理由")
    meets_threshold: bool = Field(description="閾値を満たしたか")
    improvement_suggestions: str | None = Field(
        description="改善提案(閾値未達の場合のみ)"
    )


class SelfRefinementResult(BaseModel):
    """Self-Refinement最終結果"""

    question_text: str = Field(description="質問文")
    iterations: list[RefinementIteration] = Field(description="全イテレーションの履歴")
    final_answer: str = Field(description="最終的な回答")
    final_score: float = Field(description="最終スコア", ge=1.0, le=5.0)
    success: bool = Field(description="閾値到達 or 最大試行到達")
    total_iterations: int = Field(description="実行したイテレーション数")


# ========================================
# Judge評価用の構造化出力スキーマ
# ========================================


class DirectAssessmentOutput(BaseModel):
    """Direct Assessment用のLLM出力スキーマ"""

    aspect_scores: list[AspectScore] = Field(description="各観点のスコア")
    overall_reasoning: str = Field(description="総合評価の理由")


class PairwiseOutput(BaseModel):
    """Pairwise Comparison用のLLM出力スキーマ"""

    winner: str = Field(description="勝者 ('A', 'B', 'TIE')")
    reasoning: str = Field(description="この判定をした理由")
    confidence: str = Field(description="判定の信頼度 ('high', 'medium', 'low')")


class RefinementEvaluationOutput(BaseModel):
    """Self-Refinement評価用のLLM出力スキーマ"""

    evaluation_score: float = Field(description="評価スコア", ge=1.0, le=5.0)
    evaluation_reasoning: str = Field(description="評価理由")
    improvement_suggestions: str = Field(
        description="改善提案(閾値未達の場合は具体的に、満たす場合は'なし')"
    )
