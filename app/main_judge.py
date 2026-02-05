"""LLM as a Judge デモ実行スクリプト"""

import argparse
import json
import os
from pathlib import Path

from llm_judge.direct_assessment import assess_answer
from llm_judge.pairwise_comparison import (
    compare_pair,
    compare_with_position_bias_check,
)
from llm_judge.sample_data import (
    Q1_EXCELLENT_ANSWER,
    Q1_GOOD_ANSWER,
    Q1_MEDIUM_ANSWER,
    Q1_POOR_ANSWER,
    Q3_ANSWER_A,
    Q3_ANSWER_B,
    SAMPLE_QUESTIONS,
)
from llm_judge.self_refinement import refine_with_feedback


def get_api_key() -> str:
    """環境変数からAPIキーを取得"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "環境変数 GEMINI_API_KEY が設定されていません。"
            ".envファイルを作成してください。"
        )
    return api_key


def demo_direct_assessment(api_key: str) -> None:
    """Direct Assessmentのデモ実行"""
    print("\n" + "=" * 80)
    print("Demo 1: Direct Assessment (単一回答の複数観点評価)")
    print("=" * 80 + "\n")

    question = SAMPLE_QUESTIONS[0]  # Pythonのリスト内包表記
    test_answers = [
        ("Excellent回答", Q1_EXCELLENT_ANSWER),
        ("Good回答", Q1_GOOD_ANSWER),
        ("Medium回答", Q1_MEDIUM_ANSWER),
        ("Poor回答", Q1_POOR_ANSWER),
    ]

    results = []

    for label, answer in test_answers:
        print(f"\n--- {label}を評価中 ---")
        try:
            result = assess_answer(
                question=question.text,
                answer=answer.text,
                answer_id=answer.answer_id,
                api_key=api_key,
            )

            print(f"\n✓ 評価完了: 総合スコア {result.overall_score}/5.0")
            print("\n【観点別スコア】")
            for aspect_score in result.aspect_scores:
                print(f"  - {aspect_score.aspect}: {aspect_score.score}/5")
                print(f"    理由: {aspect_score.reasoning[:80]}...")

            print(f"\n【総合評価】\n{result.overall_reasoning[:200]}...")

            results.append(result)

        except Exception as e:
            print(f"✗ エラー: {e}")

    # 結果を保存
    output_dir = Path("data/llm_judge/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "direct_assessment_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [r.model_dump() for r in results],
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n✓ 結果を保存しました: {output_file}")


def demo_pairwise_comparison(api_key: str) -> None:
    """Pairwise Comparisonのデモ実行"""
    print("\n" + "=" * 80)
    print("Demo 2: Pairwise Comparison (2つの回答を比較評価)")
    print("=" * 80 + "\n")

    question = SAMPLE_QUESTIONS[2]  # PythonとJavaScriptの違い

    print("\n--- [パターン1] 単純比較(Position bias対策なし) ---")
    try:
        result_simple = compare_pair(
            question=question.text,
            answer_a=Q3_ANSWER_A.text,
            answer_b=Q3_ANSWER_B.text,
            api_key=api_key,
        )

        print("\n✓ 比較完了")
        print(f"  勝者: {result_simple.winner}")
        print(f"  信頼度: {result_simple.confidence}")
        print(f"  理由: {result_simple.reasoning[:200]}...")

    except Exception as e:
        print(f"✗ エラー: {e}")

    print("\n--- [パターン2] Position bias対策(両方向評価) ---")
    try:
        result_aggregated = compare_with_position_bias_check(
            question=question.text,
            answer_a=Q3_ANSWER_A.text,
            answer_b=Q3_ANSWER_B.text,
            api_key=api_key,
        )

        print("\n✓ 両方向評価完了")
        print(f"  A vs B の勝者: {result_aggregated.comparison_ab.winner}")
        print(f"  B vs A の勝者: {result_aggregated.comparison_ba.winner}")
        print(f"  最終判定: {result_aggregated.final_winner}")
        print(f"  一貫性: {result_aggregated.consistency_note}")

        # 結果を保存
        output_dir = Path("data/llm_judge/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "pairwise_comparison_results.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                result_aggregated.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"\n✓ 結果を保存しました: {output_file}")

    except Exception as e:
        print(f"✗ エラー: {e}")


def demo_self_refinement(api_key: str) -> None:
    """Self-Refinementのデモ実行"""
    print("\n" + "=" * 80)
    print("Demo 3: Self-Refinement (評価→改善のイテレーション)")
    print("=" * 80 + "\n")

    question = SAMPLE_QUESTIONS[1]  # 機械学習における過学習

    try:
        result = refine_with_feedback(
            question=question.text,
            api_key=api_key,
            threshold=4.2,  # 高めの閾値
            max_iterations=3,
        )

        print("\n" + "=" * 80)
        print("最終結果")
        print("=" * 80)
        print(f"成功: {'はい' if result.success else 'いいえ'}")
        print(f"イテレーション数: {result.total_iterations}")
        print(f"最終スコア: {result.final_score:.2f}/5.0")
        print(f"\n【最終回答】\n{result.final_answer[:300]}...\n")

        print("\n【イテレーション履歴】")
        for iteration in result.iterations:
            print(f"\nイテレーション {iteration.iteration}:")
            print(f"  スコア: {iteration.evaluation_score:.2f}/5.0")
            print(f"  閾値到達: {'はい' if iteration.meets_threshold else 'いいえ'}")
            if iteration.improvement_suggestions:
                print(f"  改善提案: {iteration.improvement_suggestions[:100]}...")

        # 結果を保存
        output_dir = Path("data/llm_judge/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "self_refinement_results.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                result.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"\n✓ 結果を保存しました: {output_file}")

    except Exception as e:
        print(f"✗ エラー: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM as a Judge デモスクリプト")
    parser.add_argument(
        "--pattern",
        choices=["direct", "pairwise", "refinement", "all"],
        default="all",
        help="実行するパターン(デフォルト: all)",
    )

    args = parser.parse_args()

    try:
        api_key = get_api_key()
    except ValueError as e:
        print(f"エラー: {e}")
        return

    if args.pattern in ["direct", "all"]:
        demo_direct_assessment(api_key)

    if args.pattern in ["pairwise", "all"]:
        demo_pairwise_comparison(api_key)

    if args.pattern in ["refinement", "all"]:
        demo_self_refinement(api_key)

    print("\n" + "=" * 80)
    print("全デモ完了")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
