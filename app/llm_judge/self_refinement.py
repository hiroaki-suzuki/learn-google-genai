"""Self-Refinement: 評価→改善のイテレーションで品質向上"""

from google import genai
from google.genai import types

from llm_judge.models import (
    RefinementEvaluationOutput,
    RefinementIteration,
    SelfRefinementResult,
)
from llm_judge.prompts import (
    build_refinement_evaluator_prompt,
    build_refinement_generator_prompt,
)


def _generate_answer(
    question: str,
    feedback: str | None,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> str:
    """
    回答を生成(または改善)

    Args:
        question: 質問文
        feedback: 前回の評価フィードバック(初回はNone)
        api_key: Google GenAI APIキー
        model: 使用するモデル名

    Returns:
        str: 生成された回答
    """
    client = genai.Client(api_key=api_key)

    # プロンプト構築
    prompt = build_refinement_generator_prompt(question=question, feedback=feedback)

    try:
        # API呼び出し(通常のテキスト生成)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        if response.text is None:
            raise ValueError("API応答が空です")

        return response.text.strip()

    except Exception as e:
        print(f"  警告: 回答生成に失敗しました ({type(e).__name__}: {e})")
        raise


def _evaluate_answer(
    question: str,
    answer: str,
    threshold: float,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> RefinementEvaluationOutput:
    """
    回答を評価し、改善提案を生成

    Args:
        question: 質問文
        answer: 評価対象の回答
        threshold: 合格閾値
        api_key: Google GenAI APIキー
        model: 使用するモデル名

    Returns:
        RefinementEvaluationOutput: 評価結果と改善提案
    """
    client = genai.Client(api_key=api_key)

    # プロンプト構築
    prompt = build_refinement_evaluator_prompt(
        question=question, answer=answer, threshold=threshold
    )

    try:
        # API呼び出し
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RefinementEvaluationOutput,
            ),
        )

        if response.text is None:
            raise ValueError("API応答が空です")

        output = RefinementEvaluationOutput.model_validate_json(response.text)
        return output

    except Exception as e:
        print(f"  警告: 回答評価に失敗しました ({type(e).__name__}: {e})")
        raise


def refine_with_feedback(
    question: str,
    api_key: str,
    threshold: float = 4.0,
    max_iterations: int = 3,
    model: str = "gemini-2.0-flash",
) -> SelfRefinementResult:
    """
    Self-Refinement: 評価→改善のループで品質を段階的に向上

    Args:
        question: 質問文
        api_key: Google GenAI APIキー
        threshold: 合格閾値(1.0-5.0)
        max_iterations: 最大イテレーション数
        model: 使用するモデル名

    Returns:
        SelfRefinementResult: 全イテレーションの履歴と最終結果
    """
    iterations: list[RefinementIteration] = []
    feedback: str | None = None

    print(
        f"\n=== Self-Refinement開始 (閾値: {threshold}, "
        f"最大試行: {max_iterations}) ===\n"
    )

    for iteration in range(1, max_iterations + 1):
        print(f"--- イテレーション {iteration}/{max_iterations} ---")

        # 1. 回答生成
        print(f"  [1/2] 回答生成中{'(初回)' if iteration == 1 else '(改善中)'}...")
        generated_answer = _generate_answer(
            question=question,
            feedback=feedback,
            api_key=api_key,
            model=model,
        )

        # 2. 評価
        print("  [2/2] 評価中...")
        evaluation = _evaluate_answer(
            question=question,
            answer=generated_answer,
            threshold=threshold,
            api_key=api_key,
            model=model,
        )

        # 閾値判定
        meets_threshold = evaluation.evaluation_score >= threshold

        # イテレーション結果を記録
        iteration_result = RefinementIteration(
            iteration=iteration,
            generated_answer=generated_answer,
            evaluation_score=evaluation.evaluation_score,
            evaluation_reasoning=evaluation.evaluation_reasoning,
            meets_threshold=meets_threshold,
            improvement_suggestions=(
                evaluation.improvement_suggestions if not meets_threshold else None
            ),
        )
        iterations.append(iteration_result)

        print(
            f"  結果: スコア {evaluation.evaluation_score:.2f} "
            f"({'合格' if meets_threshold else '改善が必要'})"
        )

        # 閾値到達で終了
        if meets_threshold:
            print("\n✓ 閾値に到達しました。完了。\n")
            return SelfRefinementResult(
                question_text=question,
                iterations=iterations,
                final_answer=generated_answer,
                final_score=evaluation.evaluation_score,
                success=True,
                total_iterations=iteration,
            )

        # 次のイテレーションのためにフィードバックを準備
        feedback = evaluation.improvement_suggestions
        print(f"  フィードバック: {feedback[:100]}...\n")

    # 最大試行回数到達で終了
    print(f"\n✗ 最大試行回数({max_iterations})に到達しました。\n")
    final_iteration = iterations[-1]
    return SelfRefinementResult(
        question_text=question,
        iterations=iterations,
        final_answer=final_iteration.generated_answer,
        final_score=final_iteration.evaluation_score,
        success=False,
        total_iterations=max_iterations,
    )
