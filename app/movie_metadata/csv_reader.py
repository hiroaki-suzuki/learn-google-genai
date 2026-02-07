import csv
import logging
from pathlib import Path

from movie_metadata.models import MovieInput

logger = logging.getLogger(__name__)


class CSVReader:
    """CSV読み込みクラス

    CSVファイルから映画情報を読み込む機能を提供します。
    """

    def read(self, csv_path: Path) -> list[MovieInput]:
        """CSVファイルから映画情報を読み込む

        Args:
            csv_path: CSVファイルのパス

        Returns:
            MovieInputのリスト

        Raises:
            FileNotFoundError: CSVファイルが存在しない場合
            ValueError: CSVフォーマットが不正な場合
        """
        logger.debug(f"CSVファイルを読み込み中: {csv_path}")

        if not csv_path.exists():
            logger.error(f"CSVファイルが見つかりません: {csv_path}")
            raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")

        movies: list[MovieInput] = []

        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # ヘッダーチェック
                required_fields = {"title", "release_date", "country"}
                if not required_fields.issubset(set(reader.fieldnames or [])):
                    raise ValueError(
                        f"CSVに必要なフィールドがありません。必要: {required_fields}"
                    )

                for row_num, row in enumerate(reader, start=2):
                    try:
                        movie = MovieInput(
                            title=row["title"],
                            release_date=row["release_date"],
                            country=row["country"],
                        )
                        movies.append(movie)
                    except Exception as e:
                        logger.warning(f"行 {row_num} をスキップしました（エラー: {e}）")
                        continue

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"CSVファイルの読み込みに失敗しました: {e}")
            raise ValueError(f"CSVファイルの読み込みに失敗しました: {e}") from e

        logger.info(f"{csv_path} から {len(movies)} 件の映画を読み込みました")
        return movies
