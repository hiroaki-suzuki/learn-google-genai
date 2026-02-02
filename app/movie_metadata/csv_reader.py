import csv
from pathlib import Path

from movie_metadata.models import MovieInput


def read_movies_csv(csv_path: str) -> list[MovieInput]:
    """
    CSVファイルから映画情報を読み込む

    Args:
        csv_path: CSVファイルのパス

    Returns:
        MovieInputのリスト

    Raises:
        FileNotFoundError: CSVファイルが存在しない場合
        ValueError: CSVフォーマットが不正な場合
    """
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")

    movies: list[MovieInput] = []

    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # ヘッダーチェック
            required_fields = {"title", "release_date", "country"}
            if not required_fields.issubset(set(reader.fieldnames or [])):
                raise ValueError(
                    f"CSVに必要なフィールドがありません。必要: {required_fields}"
                )

            for row_num, row in enumerate(reader, start=2):  # ヘッダー行は1行目
                try:
                    movie = MovieInput(
                        title=row["title"],
                        release_date=row["release_date"],
                        country=row["country"],
                    )
                    movies.append(movie)
                except Exception as e:
                    print(f"警告: {row_num}行目のデータをスキップしました: {e}")
                    continue

    except Exception as e:
        raise ValueError(f"CSVファイルの読み込みに失敗しました: {e}") from e

    return movies
