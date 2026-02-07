import json
import logging
from pathlib import Path

from movie_metadata.models import MovieMetadata

logger = logging.getLogger(__name__)


class JSONWriter:
    """JSON出力クラス

    メタデータをJSON形式でファイルに出力する機能を提供します。
    """

    def write(
        self,
        metadata_list: list[MovieMetadata],
        output_path: Path,
    ) -> None:
        """メタデータをJSON形式で出力

        Args:
            metadata_list: MovieMetadataのリスト
            output_path: 出力先JSONファイルのパス

        Raises:
            OSError: ファイル書き込みに失敗した場合
        """
        logger.debug(f"Writing metadata to: {output_path}")

        # 出力ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # PydanticモデルをJSONシリアライズ可能な辞書に変換
            data = [metadata.model_dump() for metadata in metadata_list]

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,  # 日本語を正しく出力
                    indent=2,  # 整形出力
                )

            logger.info(
                f"Successfully wrote {len(metadata_list)} metadata to {output_path}"
            )

        except Exception as e:
            logger.error(f"Failed to write JSON file: {e}")
            raise OSError(f"JSONファイルの書き込みに失敗しました: {e}") from e


def write_metadata_to_json(
    metadata_list: list[MovieMetadata],
    output_path: str,
) -> None:
    """メタデータをJSON形式で出力（後方互換関数）

    Args:
        metadata_list: MovieMetadataのリスト
        output_path: 出力先JSONファイルのパス

    Raises:
        OSError: ファイル書き込みに失敗した場合
    """
    JSONWriter().write(metadata_list, Path(output_path))
