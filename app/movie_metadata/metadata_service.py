"""映画メタデータ取得サービスモジュール

CSV読込 → API取得 → JSON出力の一連のビジネスロジックを管理します。
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from movie_metadata.csv_reader import CSVReader
from movie_metadata.genai_client import GenAIClient
from movie_metadata.json_writer import JSONWriter
from movie_metadata.metadata_fetcher import fetch_movie_metadata

logger = logging.getLogger(__name__)


class ProcessResult(TypedDict):
    total: int
    success: int
    failed: int


class MetadataService:
    """映画メタデータ取得サービス

    CSV読込、API取得、JSON出力の処理フローを管理します。

    Args:
        client: GenAIClientインスタンス
        csv_reader: CSVReaderインスタンス
        json_writer: JSONWriterインスタンス
        rate_limit_sleep: API呼び出し間の待機時間（秒）
    """

    def __init__(
        self,
        client: GenAIClient,
        csv_reader: CSVReader,
        json_writer: JSONWriter,
        rate_limit_sleep: float = 1.0,
    ) -> None:
        self._client = client
        self._csv_reader = csv_reader
        self._json_writer = json_writer
        self._rate_limit_sleep = rate_limit_sleep

    def process(
        self,
        csv_path: Path,
        output_dir: Path,
    ) -> ProcessResult:
        """メタデータ取得処理を実行する

        Args:
            csv_path: 入力CSVファイルのパス
            output_dir: JSON出力ディレクトリ

        Returns:
            処理結果の辞書（total, success, failed）
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # CSV読み込み
        movies = self._csv_reader.read(csv_path)
        logger.info(f"Loaded {len(movies)} movies from CSV")

        # 各映画のメタデータを取得
        metadata_list = []
        total = len(movies)
        failed_count = 0

        for i, movie in enumerate(movies, start=1):
            logger.info(f"Processing [{i}/{total}]: {movie.title}")

            try:
                metadata = fetch_movie_metadata(movie, self._client)
                metadata_list.append(metadata)

                # レート制限対策: 最後の映画以外は待機
                if i < total:
                    time.sleep(self._rate_limit_sleep)

            except Exception as e:
                logger.error(f"Failed to fetch metadata for {movie.title}: {e}")
                failed_count += 1
                continue

        # JSON出力
        if metadata_list:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"movie_metadata_{timestamp}.json"
            self._json_writer.write(metadata_list, output_path)
            logger.info(
                f"=== 完了: {len(metadata_list)}/{total}件成功, "
                f"{failed_count}件失敗 ==="
            )
        else:
            logger.error("エラー: メタデータを取得できませんでした")

        return ProcessResult(
            total=total,
            success=len(metadata_list),
            failed=failed_count,
        )
