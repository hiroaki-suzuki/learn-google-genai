"""json_writerモジュールのテスト"""

import json
from pathlib import Path

import pytest

from movie_metadata.json_writer import JSONWriter
from movie_metadata.models import MovieMetadata


def test_write_metadata_to_json(
    tmp_path: Path, sample_movie_metadata: MovieMetadata
) -> None:
    """正常なJSON書き込みテスト"""
    # Arrange
    output_file = tmp_path / "output.json"
    writer = JSONWriter()

    # Act
    writer.write([sample_movie_metadata], output_file)

    # Assert
    assert output_file.exists()
    with output_file.open(encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["title"] == "Test Movie"
    assert data[0]["japanese_titles"] == ["テスト映画"]


def test_write_metadata_to_json_multiple_items(tmp_path: Path) -> None:
    """複数アイテムのJSON書き込みテスト"""
    # Arrange
    metadata_list = [
        MovieMetadata(
            title=f"Movie {i}",
            japanese_titles=[f"映画{i}"],
            original_work="オリジナル",
            original_authors=[],
            release_date=f"2024-0{i}-01",
            country="Japan",
            distributor="配給社",
            production_companies=["制作会社"],
            box_office="$1M",
            cast=["俳優"],
            screenwriters=["脚本家"],
            music=["作曲家"],
            voice_actors=["声優"],
        )
        for i in range(1, 4)
    ]
    output_file = tmp_path / "output.json"
    writer = JSONWriter()

    # Act
    writer.write(metadata_list, output_file)

    # Assert
    assert output_file.exists()
    with output_file.open(encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 3
    assert data[0]["title"] == "Movie 1"
    assert data[2]["title"] == "Movie 3"


def test_write_metadata_to_json_creates_directory(
    tmp_path: Path, sample_movie_metadata: MovieMetadata
) -> None:
    """ディレクトリが存在しない場合に作成するテスト"""
    # Arrange
    output_file = tmp_path / "subdir" / "nested" / "output.json"
    writer = JSONWriter()

    # Act
    writer.write([sample_movie_metadata], output_file)

    # Assert
    assert output_file.exists()
    assert output_file.parent.exists()


def test_write_metadata_to_json_japanese_characters(tmp_path: Path) -> None:
    """日本語文字が正しく出力されるテスト"""
    # Arrange
    metadata = MovieMetadata(
        title="千と千尋の神隠し",
        japanese_titles=["千と千尋の神隠し", "Sen to Chihiro no Kamikakushi"],
        original_work="オリジナル",
        original_authors=[],
        release_date="2001-07-20",
        country="日本",
        distributor="東宝",
        production_companies=["スタジオジブリ"],
        box_office="308億円",
        cast=["柊瑠美", "入野自由"],
        screenwriters=["宮崎駿"],
        music=["久石譲"],
        voice_actors=["柊瑠美", "入野自由"],
    )
    output_file = tmp_path / "output.json"
    writer = JSONWriter()

    # Act
    writer.write([metadata], output_file)

    # Assert
    with output_file.open(encoding="utf-8") as f:
        content = f.read()
        data = json.loads(content)
    assert data[0]["title"] == "千と千尋の神隠し"
    assert data[0]["country"] == "日本"
    # ensure_ascii=Falseが機能しているか確認
    assert "千と千尋の神隠し" in content  # エスケープされていないことを確認


def test_write_metadata_to_json_write_error(
    tmp_path: Path, sample_movie_metadata: MovieMetadata
) -> None:
    """ファイル書き込み失敗時の例外処理テスト"""
    # Arrange
    output_file = tmp_path / "readonly_dir" / "output.json"
    output_file.parent.mkdir()
    # 親ディレクトリを読み取り専用にしてファイル作成を不可能にする
    output_file.parent.chmod(0o444)
    writer = JSONWriter()

    # Act & Assert
    try:
        with pytest.raises(OSError, match="JSONファイルの書き込みに失敗しました"):
            writer.write([sample_movie_metadata], output_file)
    finally:
        # クリーンアップ: パーミッションを復元
        output_file.parent.chmod(0o755)
