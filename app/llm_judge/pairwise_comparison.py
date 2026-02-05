"""Pairwise Comparison: 2つの回答を比較評価"""

from google import genai
from google.genai import types

from llm_judge.models import (
    PairwiseAggregatedResult,
    PairwiseComparisonResult,
    PairwiseOutput,
)
from llm_judge.prompts import build_pairwise_comparison_prompt


def _compare_single(
    question: str,
    answer_a: str,
    answer_b: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> PairwiseComparisonResult:
    """
    1回のPairwise Comparison評価

    Args:
        question: 質問文
        answer_a: 回答A
        answer_b: 回答B
        api_key: Google GenAI APIキー
        model: 使用するモデル名

    Returns:
        PairwiseComparisonResult: 比較結果
    """
    client = genai.Client(api_key=api_key)

    # プロンプト構築
    prompt = build_pairwise_comparison_prompt(
        question=question, answer_a=answer_a, answer_b=answer_b
    )

    try:
        # API呼び出し
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PairwiseOutput,
            ),
        )

        # Pydanticモデルでパース
        if response.text is None:
            raise ValueError("API応答が空です")

        output = PairwiseOutput.model_validate_json(response.text)

        return PairwiseComparisonResult(
            winner=output.winner,
            reasoning=output.reasoning,
            confidence=output.confidence,
        )

    except Exception as e:
        print(
            f"  警告: Pairwise Comparison評価に失敗しました ({type(e).__name__}: {e})"
        )
        raise


def compare_pair(
    question: str,
    answer_a: str,
    answer_b: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> PairwiseComparisonResult:
    """
    2つの回答を比較評価(単純版、Position bias対策なし)

    Args:
        question: 質問文
        answer_a: 回答A
        answer_b: 回答B
        api_key: Google GenAI APIキー
        model: 使用するモデル名

    Returns:
        PairwiseComparisonResult: 比較結果
    """
    return _compare_single(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        api_key=api_key,
        model=model,
    )


def compare_with_position_bias_check(
    question: str,
    answer_a: str,
    answer_b: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> PairwiseAggregatedResult:
    """
    Position bias対策: A-B と B-A の両方向で評価

    Args:
        question: 質問文
        answer_a: 回答A
        answer_b: 回答B
        api_key: Google GenAI APIキー
        model: 使用するモデル名

    Returns:
        PairwiseAggregatedResult: 集約結果(両方向の比較 + 一貫性チェック)
    """
    print("  [1/2] A vs B を評価中...")
    comparison_ab = _compare_single(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        api_key=api_key,
        model=model,
    )

    print("  [2/2] B vs A を評価中(Position bias対策)...")
    comparison_ba = _compare_single(
        question=question,
        answer_a=answer_b,  # 順序を入れ替え
        answer_b=answer_a,
        api_key=api_key,
        model=model,
    )

    # 一貫性チェック
    final_winner, consistency_note = _check_consistency(comparison_ab, comparison_ba)

    return PairwiseAggregatedResult(
        comparison_ab=comparison_ab,
        comparison_ba=comparison_ba,
        final_winner=final_winner,
        consistency_note=consistency_note,
    )


def _check_consistency(
    comparison_ab: PairwiseComparisonResult,
    comparison_ba: PairwiseComparisonResult,
) -> tuple[str, str]:
    """
    A-B と B-A の評価結果の一貫性をチェック

    Args:
        comparison_ab: A vs B の結果
        comparison_ba: B vs A の結果

    Returns:
        tuple[str, str]: (最終的な勝者, 一貫性に関する説明)
    """
    winner_ab = comparison_ab.winner
    winner_ba = comparison_ba.winner

    # B vs A の結果を A vs B の視点に変換
    # B vs A で 'A' が勝った場合、A vs B では 'B' が勝ったことを意味する
    winner_ba_flipped = _flip_winner(winner_ba)

    # 一貫性チェック
    if winner_ab == winner_ba_flipped:
        # 一貫している
        if winner_ab == "TIE":
            return "TIE", "両方向で同等と判定されました(一貫性あり)"
        else:
            return (
                winner_ab,
                f"両方向で{winner_ab}が優れていると判定されました(一貫性あり)",
            )
    else:
        # 不一致(Position biasの可能性)
        return (
            "INCONSISTENT",
            f"評価が不一致です(A vs B: {winner_ab}, B vs A: {winner_ba})"
            " - Position biasの可能性があります",
        )


def _flip_winner(winner: str) -> str:
    """B vs A の結果を A vs B の視点に変換"""
    if winner == "A":
        return "B"
    elif winner == "B":
        return "A"
    else:  # TIE
        return "TIE"
