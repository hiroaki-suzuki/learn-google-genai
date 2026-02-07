"""映画メタ情報の品質評価・改善ループシステムのメインスクリプト

CSVから映画情報を読み込み、LLM as a Judgeを使用してメタデータの品質を評価し、
基準を満たすまで改善を繰り返します。
"""

import logging
import time
from pathlib import Path

from config import AppConfig
from logging_config import setup_logging
from movie_metadata.csv_reader import CSVReader
from movie_metadata.models import BatchRefinementResult
from movie_metadata.refinement_writer import RefinementResultWriter
from movie_metadata.refiner import MetadataRefiner

logger = logging.getLogger(__name__)


def main() -> None:
    """映画メタ情報の品質評価・改善ループシステムのメインエントリーポイント"""
    # 設定読み込み
    config = AppConfig()

    # ロギング設定
    setup_logging(config.log_level)
    logger.info("=== 映画メタ情報品質評価・改善ループシステム起動 ===")

    # パス設定
    csv_path = Path(__file__).parent / config.csv_path
    output_dir = Path(__file__).parent / config.output_dir

    # CSVから映画情報を読み込み
    csv_reader = CSVReader()
    try:
        movies = csv_reader.read(csv_path)
        if not movies:
            logger.error("CSVファイルに映画情報が含まれていません")
            return

    except Exception as e:
        logger.error(f"CSVファイルの読み込みに失敗しました: {e}")
        return

    # メタデータ改善ループを実行
    try:
        refiner = MetadataRefiner(
            api_key=config.gemini_api_key,
            model_name=config.model_name,
            rate_limit_sleep=config.rate_limit_sleep,
        )

        logger.info("評価・改善ループを開始します")
        start_time = time.perf_counter()
        total_count = len(movies)
        results = []
        errors = []

        writer = RefinementResultWriter()

        for index, movie_input in enumerate(movies, start=1):
            logger.info(
                f"処理中: {index}/{total_count}件完了（タイトル: {movie_input.title}）"
            )
            logger.info(
                f"処理対象: {movie_input.title} ({movie_input.country}, "
                f"{movie_input.release_date})"
            )

            try:
                result = refiner.refine(
                    movie_input=movie_input,
                    max_iterations=3,
                    threshold=3.5,
                )
                results.append(result)

                # 最終結果をコンソールに表示
                logger.info("=== 最終結果 ===")
                logger.info(f"成功: {result.success}")
                logger.info(f"総イテレーション数: {result.total_iterations}")

                # 各イテレーションのスコアを表示
                for i, entry in enumerate(result.history, start=1):
                    logger.info(f"\nイテレーション {i}:")
                    for field_score in entry.evaluation.field_scores:
                        logger.info(
                            f"  - {field_score.field_name}: {field_score.score:.2f}"
                        )
                    logger.info(f"  ステータス: {entry.evaluation.overall_status}")

                # 最終スコアサマリー
                final_entry = result.history[-1]
                logger.info("\n=== 最終スコア ===")
                for field_score in final_entry.evaluation.field_scores:
                    status = "✓" if field_score.score >= 3.5 else "✗"
                    logger.info(
                        f"{status} {field_score.field_name}: {field_score.score:.2f}"
                    )
            except Exception as e:
                logger.error("処理中にエラーが発生しました: %s", e, exc_info=True)
                errors.append({"title": movie_input.title, "message": str(e)})
                continue

        total_time = time.perf_counter() - start_time
        logger.info(f"総処理時間: {total_time:.2f}秒")

        success_count = sum(result.success for result in results)
        error_count = len(errors)
        batch_result = BatchRefinementResult(
            results=results,
            total_count=total_count,
            success_count=success_count,
            error_count=error_count,
            errors=errors,
            processing_time=total_time,
        )
        writer.write_batch(batch_result, output_dir)
        logger.info(f"バッチ結果をJSON形式で保存しました: {output_dir}")

        if errors:
            error_titles = ", ".join(error["title"] for error in errors)
            logger.error(f"エラー件数: {error_count}")
            logger.error(f"エラーが発生した映画: {error_titles}")

    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {e}", exc_info=True)
        return


if __name__ == "__main__":
    main()
