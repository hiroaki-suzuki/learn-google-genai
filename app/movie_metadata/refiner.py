"""メタデータ改善ループ機能

評価→改善提案→再取得のサイクルを自動的に繰り返す機能を提供します。
"""

import logging
import time

from movie_metadata.evaluator import MetadataEvaluator
from movie_metadata.genai_client import GenAIClient
from movie_metadata.improvement_proposer import ImprovementProposer
from movie_metadata.metadata_fetcher import MovieMetadataFetcher
from movie_metadata.models import (
    MetadataRefinementResult,
    MovieInput,
    RefinementHistoryEntry,
)

logger = logging.getLogger(__name__)


class MetadataRefiner:
    """メタデータ改善ループクラス

    評価→改善提案→再取得のサイクルを自動的に繰り返し、
    すべてのフィールドが閾値以上になるまで改善を試みます。

    Args:
        api_key: Google GenAI APIキー
        model_name: 使用するモデル名（デフォルト: gemini-2.0-flash）
        rate_limit_sleep: API呼び出し間のスリープ時間（秒）

    Examples:
        refiner = MetadataRefiner(api_key="YOUR_KEY")
        result = refiner.refine(movie_input, max_iterations=3, threshold=3.5)
        print(f"Success: {result.success}, Iterations: {result.total_iterations}")
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash",
        rate_limit_sleep: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.rate_limit_sleep = rate_limit_sleep

        # 評価器と改善提案器を初期化
        self.evaluator = MetadataEvaluator(api_key=api_key, model_name=model_name)
        self.proposer = ImprovementProposer(api_key=api_key, model_name=model_name)

        logger.info(
            f"MetadataRefinerを初期化しました（モデル: {model_name}, "
            f"レート制限スリープ: {rate_limit_sleep}秒）"
        )

    def refine(
        self,
        movie_input: MovieInput,
        max_iterations: int = 3,
        threshold: float = 3.5,
    ) -> MetadataRefinementResult:
        """メタデータを改善する

        すべてのフィールドスコアが閾値以上になるまで、
        または最大イテレーション数に達するまで改善を繰り返します。

        Args:
            movie_input: 映画の基本情報
            max_iterations: 最大イテレーション数（デフォルト: 3）
            threshold: 各フィールドの合格閾値（デフォルト: 3.5）

        Returns:
            MetadataRefinementResult: 改善プロセスの結果

        Raises:
            Exception: メタデータ取得、評価、改善提案のいずれかに失敗した場合
        """
        logger.info(
            f"メタデータ改善ループを開始します（最大イテレーション: {max_iterations}, "
            f"閾値: {threshold}, タイトル: {movie_input.title}）"
        )

        history = []

        # GenAIClientをコンテキストマネージャーとして使用
        with GenAIClient(api_key=self.api_key, model_name=self.model_name) as client:
            fetcher = MovieMetadataFetcher(client)

            for iteration in range(1, max_iterations + 1):
                logger.info(f"イテレーション {iteration} を開始します")

                # 1. メタデータ取得
                if iteration == 1:
                    # 初回は通常の取得
                    metadata = fetcher.fetch(movie_input)
                else:
                    # 2回目以降は改善提案を使って再取得
                    prev_entry = history[-1]
                    improvement_instruction = (
                        prev_entry.evaluation.improvement_suggestions
                    )
                    metadata = fetcher.fetch_with_improvement(
                        movie_input, improvement_instruction
                    )

                # レート制限対策のスリープ
                time.sleep(self.rate_limit_sleep)

                # 2. メタデータ評価
                evaluation = self.evaluator.evaluate(metadata, iteration)

                # レート制限対策のスリープ
                time.sleep(self.rate_limit_sleep)

                # 3. 履歴に追加
                entry = RefinementHistoryEntry(
                    iteration=iteration,
                    metadata=metadata,
                    evaluation=evaluation,
                )
                history.append(entry)

                # 4. 終了条件チェック
                if evaluation.overall_status == "pass":
                    logger.info(
                        f"すべてのフィールドが閾値{threshold}以上を達成しました"
                    )
                    return MetadataRefinementResult(
                        final_metadata=metadata,
                        history=history,
                        success=True,
                        total_iterations=iteration,
                    )

                # 5. 最大イテレーション数に達したかチェック
                if iteration >= max_iterations:
                    logger.warning(
                        f"最大イテレーション数{max_iterations}に達しました。"
                        f"一部のフィールドが閾値{threshold}未満です。"
                    )
                    return MetadataRefinementResult(
                        final_metadata=metadata,
                        history=history,
                        success=False,
                        total_iterations=iteration,
                    )

                # 6. 次のイテレーションのために改善提案を生成
                logger.info(
                    f"イテレーション {iteration + 1} のために改善提案を生成します"
                )
                self.proposer.propose(movie_input, metadata, evaluation)

                # レート制限対策のスリープ（次のイテレーションの前）
                time.sleep(self.rate_limit_sleep)

        # このコードには到達しないはずだが、念のため
        msg = "予期しないエラー: ループ終了条件に達しませんでした"
        raise RuntimeError(msg)
