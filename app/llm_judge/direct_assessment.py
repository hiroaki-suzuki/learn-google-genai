"""Direct Assessment: 単一回答を複数観点で評価"""

from google import genai
from google.genai import types

from llm_judge.models import DirectAssessmentOutput, DirectAssessmentResult
from llm_judge.prompts import build_direct_assessment_prompt


def assess_answer(
    question: str,
    answer: str,
    answer_id: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> DirectAssessmentResult:
    """
    Direct Assessment: 単一回答を複数観点で評価

    Args:
        question: 質問文
        answer: 評価対象の回答
        answer_id: 回答ID
        api_key: Google GenAI APIキー
        model: 使用するモデル名

    Returns:
        DirectAssessmentResult: 評価結果

    Raises:
        Exception: API呼び出しまたはパースに失敗した場合
    """
    client = genai.Client(api_key=api_key)

    # プロンプト構築
    prompt = build_direct_assessment_prompt(question=question, answer=answer)

    try:
        # API呼び出し
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DirectAssessmentOutput,
            ),
        )

        # Pydanticモデルでパース
        if response.text is None:
            raise ValueError("API応答が空です")

        output = DirectAssessmentOutput.model_validate_json(response.text)

        # 総合スコアを計算(全観点の平均)
        overall_score = sum(s.score for s in output.aspect_scores) / len(
            output.aspect_scores
        )

        # 結果オブジェクトを構築
        result = DirectAssessmentResult(
            answer_id=answer_id,
            question_text=question,
            answer_text=answer,
            aspect_scores=output.aspect_scores,
            overall_score=round(overall_score, 2),
            overall_reasoning=output.overall_reasoning,
        )

        return result

    except Exception as e:
        print(f"  警告: Direct Assessment評価に失敗しました ({type(e).__name__}: {e})")
        raise
