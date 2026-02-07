"""メタデータ評価機能

MovieMetadataの各項目をLLM as a Judge（Direct Assessment）で評価する機能を提供します。
"""

import logging

from movie_metadata.genai_client import GenAIClient
from movie_metadata.models import (
    MetadataEvaluationOutput,
    MetadataEvaluationResult,
    MovieMetadata,
)
from movie_metadata.prompts import build_metadata_evaluation_prompt

logger = logging.getLogger(__name__)


class MetadataEvaluator:
    """メタデータ評価クラス

    MovieMetadataの各フィールドをLLMで評価し、品質スコアと改善提案を生成します。

    Args:
        api_key: Google GenAI APIキー
        model_name: 使用するモデル名（デフォルト: gemini-2.0-flash）

    Examples:
        evaluator = MetadataEvaluator(api_key="YOUR_KEY")
        result = evaluator.evaluate(metadata, iteration=1)
        print(f"Overall status: {result.overall_status}")
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key
        self.model_name = model_name
        logger.info(f"MetadataEvaluatorを初期化しました（モデル: {model_name}）")

    def evaluate(
        self, metadata: MovieMetadata, iteration: int = 1
    ) -> MetadataEvaluationResult:
        """メタデータを評価する

        Args:
            metadata: 評価対象のメタデータ
            iteration: イテレーション番号（デフォルト: 1）

        Returns:
            MetadataEvaluationResult: 評価結果

        Raises:
            ValueError: API応答が空の場合
            Exception: API呼び出しまたはパースに失敗した場合
        """
        logger.info(
            f"メタデータ評価を開始します（イテレーション: {iteration}, "
            f"タイトル: {metadata.title}）"
        )

        # 1. プロンプト構築
        prompt = build_metadata_evaluation_prompt(
            title=metadata.title,
            release_date=metadata.release_date,
            country=metadata.country,
            japanese_titles=metadata.japanese_titles,
            original_work=metadata.original_work,
            original_authors=metadata.original_authors,
            distributor=metadata.distributor,
            production_companies=metadata.production_companies,
            box_office=metadata.box_office,
            cast=metadata.cast,
            screenwriters=metadata.screenwriters,
            music=metadata.music,
            voice_actors=metadata.voice_actors,
        )

        # 2. GenAIClientで評価実行
        with GenAIClient(api_key=self.api_key, model_name=self.model_name) as client:
            try:
                response_text = client.generate_content(
                    prompt=prompt,
                    response_schema=MetadataEvaluationOutput,
                )

                # 3. パース
                output = MetadataEvaluationOutput.model_validate_json(response_text)

                logger.debug(
                    f"評価完了: {len(output.field_scores)}個のフィールドを評価"
                )

            except Exception as e:
                logger.error(f"メタデータ評価に失敗しました ({type(e).__name__}: {e})")
                raise

        # 4. overall_statusを計算
        # すべてのフィールドが3.5以上なら"pass"、1つでも3.5未満なら"fail"
        all_pass = all(score.score >= 3.5 for score in output.field_scores)
        overall_status = "pass" if all_pass else "fail"

        # 平均スコアを計算
        avg_score = sum(s.score for s in output.field_scores) / len(output.field_scores)
        logger.info(f"評価結果: {overall_status} (平均スコア: {avg_score:.2f})")

        # 5. MetadataEvaluationResultを構築して返す
        return MetadataEvaluationResult(
            iteration=iteration,
            field_scores=output.field_scores,
            overall_status=overall_status,
            improvement_suggestions=output.improvement_suggestions,
        )
