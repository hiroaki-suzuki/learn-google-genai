"""メタデータ改善提案機能

評価結果に基づいてメタデータの改善方法を提案する機能を提供します。
"""

import logging

from movie_metadata.genai_client import GenAIClient
from movie_metadata.models import (
    MetadataEvaluationResult,
    MovieInput,
    MovieMetadata,
)
from movie_metadata.prompts import build_improvement_proposal_prompt

logger = logging.getLogger(__name__)


class ImprovementProposer:
    """メタデータ改善提案クラス

    評価結果に基づいて、メタデータを改善するための具体的な提案を生成します。

    Args:
        api_key: Google GenAI APIキー
        model_name: 使用するモデル名（デフォルト: gemini-2.0-flash）
        threshold: 品質スコアの閾値（デフォルト: 4.0）

    Examples:
        proposer = ImprovementProposer(api_key="YOUR_KEY", threshold=4.0)
        proposal = proposer.propose(movie_input, metadata, evaluation)
        print(proposal)
    """

    def __init__(
        self, api_key: str, model_name: str = "gemini-2.0-flash", threshold: float = 4.0
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.threshold = threshold
        logger.info(
            f"ImprovementProposerを初期化しました（モデル: {model_name}, "
            f"閾値: {threshold}）"
        )

    def propose(
        self,
        movie_input: MovieInput,
        current_metadata: MovieMetadata,
        evaluation: MetadataEvaluationResult,
    ) -> str:
        """改善提案を生成する

        Args:
            movie_input: 映画の基本情報
            current_metadata: 現在のメタデータ
            evaluation: 評価結果

        Returns:
            改善提案の文字列

        Raises:
            ValueError: API応答が空の場合
            Exception: API呼び出しに失敗した場合
        """
        logger.info(
            f"改善提案を生成中（イテレーション: {evaluation.iteration}, "
            f"タイトル: {movie_input.title}）"
        )

        # すべてのフィールドが閾値以上の場合は提案不要
        if evaluation.overall_status == "pass":
            logger.info("すべてのフィールドが閾値以上です。改善の必要はありません。")
            return "改善の必要なし"

        # 1. プロンプト構築
        prompt = build_improvement_proposal_prompt(
            movie_input=movie_input,
            current_metadata=current_metadata,
            evaluation=evaluation,
            threshold=self.threshold,
        )

        # 2. GenAIClientで改善提案を生成
        with GenAIClient(api_key=self.api_key, model_name=self.model_name) as client:
            try:
                proposal = client.generate_content(prompt=prompt)
                logger.info("改善提案を生成しました")
                logger.debug(f"提案内容（一部）: {proposal[:200]}...")
                return proposal

            except Exception as e:
                logger.error(f"改善提案の生成に失敗しました ({type(e).__name__}: {e})")
                raise
