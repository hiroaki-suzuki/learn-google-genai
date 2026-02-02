import json
from pathlib import Path

from movie_metadata.models import MovieMetadata


def write_metadata_to_json(
    metadata_list: list[MovieMetadata],
    output_path: str,
) -> None:
    """
    メタデータをJSON形式で出力

    Args:
        metadata_list: MovieMetadataのリスト
        output_path: 出力先JSONファイルのパス

    Raises:
        IOError: ファイル書き込みに失敗した場合
    """
    path = Path(output_path)

    # 出力ディレクトリが存在しない場合は作成
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # PydanticモデルをJSONシリアライズ可能な辞書に変換
        data = [metadata.model_dump() for metadata in metadata_list]

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,  # 日本語を正しく出力
                indent=2,  # 整形出力
            )

        print(f"\n✓ メタデータを出力しました: {output_path}")

    except Exception as e:
        raise IOError(f"JSONファイルの書き込みに失敗しました: {e}") from e
