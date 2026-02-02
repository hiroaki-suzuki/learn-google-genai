import os
import time
from datetime import datetime
from pathlib import Path

from movie_metadata.csv_reader import read_movies_csv
from movie_metadata.json_writer import write_metadata_to_json
from movie_metadata.metadata_fetcher import fetch_movie_metadata


def main():
    """映画メタ情報取得システムのメインエントリーポイント"""
    print("=== 映画メタ情報取得システム ===\n")

    # 環境変数からAPIキー取得
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("エラー: GEMINI_API_KEYが設定されていません")
        return

    # パス設定
    csv_path = Path(__file__).parent / "data" / "movies_test3.csv"
    output_dir = Path(__file__).parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV読み込み
    try:
        movies = read_movies_csv(str(csv_path))
        print(f"✓ {len(movies)}件の映画情報を読み込みました\n")
    except Exception as e:
        print(f"エラー: {e}")
        return

    # 各映画のメタデータを取得
    metadata_list = []
    total = len(movies)

    for i, movie in enumerate(movies, start=1):
        print(f"[{i}/{total}] {movie.title} のメタデータを取得中...")

        try:
            metadata = fetch_movie_metadata(movie, api_key)
            metadata_list.append(metadata)
            print("  ✓ 取得完了")

            # レート制限対策: 最後の映画以外は1秒待機
            if i < total:
                time.sleep(1)

        except Exception as e:
            print(f"  ✗ エラー: {e}")
            continue

    # JSON出力
    if metadata_list:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"movie_metadata_{timestamp}.json"
        write_metadata_to_json(metadata_list, str(output_path))
        print(
            f"\n=== 完了: {len(metadata_list)}/{total}件のメタデータを取得しました ==="
        )
    else:
        print("\nエラー: メタデータを取得できませんでした")


if __name__ == "__main__":
    main()
