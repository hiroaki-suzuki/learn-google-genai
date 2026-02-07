import logging
from pathlib import Path

from config import AppConfig
from logging_config import setup_logging
from movie_metadata.csv_reader import CSVReader
from movie_metadata.genai_client import GenAIClient
from movie_metadata.json_writer import JSONWriter
from movie_metadata.metadata_service import MetadataService

logger = logging.getLogger(__name__)


def main() -> None:
    """映画メタ情報取得システムのメインエントリーポイント"""
    # 設定読み込み
    config = AppConfig()

    # ロギング設定
    setup_logging(config.log_level)
    logger.info("=== 映画メタ情報取得システム起動 ===")

    # コンテキストマネージャーでクライアントを管理
    with GenAIClient(
        api_key=config.gemini_api_key,
        model_name=config.model_name,
    ) as client:
        # 依存コンポーネントの初期化
        csv_reader = CSVReader()
        json_writer = JSONWriter()

        # サービス初期化（依存性注入）
        service = MetadataService(
            client=client,
            csv_reader=csv_reader,
            json_writer=json_writer,
            rate_limit_sleep=config.rate_limit_sleep,
        )

        # パス設定
        csv_path = Path(__file__).parent / config.csv_path
        output_dir = Path(__file__).parent / config.output_dir

        # 処理実行
        try:
            result = service.process(csv_path, output_dir)
            logger.info(
                f"処理結果: {result['success']}/{result['total']}件成功, "
                f"{result['failed']}件失敗"
            )
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")


if __name__ == "__main__":
    main()
