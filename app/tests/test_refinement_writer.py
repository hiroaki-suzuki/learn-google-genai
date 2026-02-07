"""refinement_writer.pyの単体テスト"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from movie_metadata.models import (
    BatchRefinementResult,
    MetadataEvaluationResult,
    MetadataFieldScore,
    MetadataRefinementResult,
    MovieMetadata,
    RefinementHistoryEntry,
)
from movie_metadata.refinement_writer import RefinementResultWriter


@pytest.fixture
def sample_refinement_result() -> MetadataRefinementResult:
    """テスト用MetadataRefinementResultフィクスチャ"""
    metadata = MovieMetadata(
        title="Test Movie",
        japanese_titles=["テスト映画"],
        release_date="2024-01-01",
        country="Japan",
        distributor="テスト配給",
        box_office="$1M",
        cast=["俳優A"],
        music=["作曲家B"],
        voice_actors=["声優C"],
    )
    evaluation = MetadataEvaluationResult(
        iteration=1,
        field_scores=[
            MetadataFieldScore(
                field_name="title",
                score=4.0,
                reasoning="タイトルは適切です",
            )
        ],
        overall_status="pass",
        improvement_suggestions="なし",
    )
    history = [
        RefinementHistoryEntry(
            iteration=1,
            metadata=metadata,
            evaluation=evaluation,
        )
    ]
    return MetadataRefinementResult(
        final_metadata=metadata,
        history=history,
        success=True,
        total_iterations=1,
    )


@pytest.fixture
def sample_batch_result(
    sample_refinement_result: MetadataRefinementResult,
) -> BatchRefinementResult:
    """テスト用BatchRefinementResultフィクスチャ"""
    return BatchRefinementResult(
        results=[sample_refinement_result],
        total_count=1,
        success_count=1,
        error_count=0,
        errors=[],
        processing_time=12.5,
    )


class TestRefinementResultWriter:
    """RefinementResultWriterクラスのテスト"""

    def test_write_creates_json_file(
        self, tmp_path: Path, sample_refinement_result: MetadataRefinementResult
    ) -> None:
        """write()メソッドがJSONファイルを作成することをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"

        writer.write(sample_refinement_result, output_dir)

        # ファイルが作成されたことを確認
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 1

        # ファイル名のフォーマットを確認
        filename = json_files[0].name
        assert filename.startswith("Test_Movie_refinement_")
        assert filename.endswith(".json")

    def test_write_creates_directory_if_not_exists(
        self, tmp_path: Path, sample_refinement_result: MetadataRefinementResult
    ) -> None:
        """ディレクトリが存在しない場合に自動作成されることをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "nested" / "output" / "dir"

        # ディレクトリが存在しないことを確認
        assert not output_dir.exists()

        writer.write(sample_refinement_result, output_dir)

        # ディレクトリが作成されたことを確認
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_write_json_content_is_valid(
        self, tmp_path: Path, sample_refinement_result: MetadataRefinementResult
    ) -> None:
        """出力されたJSONファイルの内容が正しいことをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"

        writer.write(sample_refinement_result, output_dir)

        # JSONファイルを読み込み
        json_files = list(output_dir.glob("*.json"))
        with json_files[0].open("r", encoding="utf-8") as f:
            data = json.load(f)

        # JSONの内容を検証
        assert data["final_metadata"]["title"] == "Test Movie"
        assert data["success"] is True
        assert data["total_iterations"] == 1
        assert len(data["history"]) == 1
        assert data["history"][0]["iteration"] == 1

    def test_write_json_is_utf8_encoded(
        self, tmp_path: Path, sample_refinement_result: MetadataRefinementResult
    ) -> None:
        """JSONファイルがUTF-8エンコーディングで出力されることをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"

        writer.write(sample_refinement_result, output_dir)

        # JSONファイルを読み込み
        json_files = list(output_dir.glob("*.json"))
        with json_files[0].open("r", encoding="utf-8") as f:
            data = json.load(f)

        # 日本語が正しく読み込めることを確認
        assert data["final_metadata"]["japanese_titles"][0] == "テスト映画"

    def test_sanitize_filename_replaces_spaces(self) -> None:
        """_sanitize_filename()メソッドがスペースをアンダースコアに置換することをテスト"""
        writer = RefinementResultWriter()
        result = writer._sanitize_filename("Test Movie Title")
        assert result == "Test_Movie_Title"

    def test_sanitize_filename_removes_invalid_characters(self) -> None:
        """_sanitize_filename()メソッドが無効な文字を削除することをテスト"""
        writer = RefinementResultWriter()
        result = writer._sanitize_filename('Test<>:"/\\|?*Movie')
        assert result == "TestMovie"

    def test_sanitize_filename_truncates_long_titles(self) -> None:
        """_sanitize_filename()メソッドが長いタイトルを切り詰めることをテスト"""
        writer = RefinementResultWriter()
        long_title = "A" * 100
        result = writer._sanitize_filename(long_title)
        assert len(result) == 50

    def test_sanitize_filename_handles_mixed_cases(self) -> None:
        """_sanitize_filename()メソッドが複合的なケースを処理することをテスト"""
        writer = RefinementResultWriter()
        result = writer._sanitize_filename('Test <Movie>: "Title" 2024')
        assert result == "Test_Movie_Title_2024"

    def test_write_raises_exception_on_file_write_error(
        self, tmp_path: Path, sample_refinement_result: MetadataRefinementResult
    ) -> None:
        """ファイル書き込み失敗時に例外を発生させることをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"

        # mock_openを使用して書き込みエラーをシミュレート
        with patch("pathlib.Path.open", mock_open()) as mock_file:
            mock_file.side_effect = OSError("書き込みエラー")

            with pytest.raises(OSError, match="書き込みエラー"):
                writer.write(sample_refinement_result, output_dir)

    def test_write_with_existing_directory(
        self, tmp_path: Path, sample_refinement_result: MetadataRefinementResult
    ) -> None:
        """既存のディレクトリに書き込めることをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 既存のディレクトリに書き込み
        writer.write(sample_refinement_result, output_dir)

        # ファイルが作成されたことを確認
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 1

    def test_write_batch_creates_json_file(
        self, tmp_path: Path, sample_batch_result: BatchRefinementResult
    ) -> None:
        """write_batch()メソッドがJSONファイルを作成することをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"

        writer.write_batch(sample_batch_result, output_dir)

        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 1
        assert json_files[0].name.startswith("batch_refinement_result_")
        assert json_files[0].name.endswith(".json")

    def test_write_batch_creates_directory_if_not_exists(
        self, tmp_path: Path, sample_batch_result: BatchRefinementResult
    ) -> None:
        """write_batch()がディレクトリを作成することをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "nested" / "output" / "dir"

        assert not output_dir.exists()

        writer.write_batch(sample_batch_result, output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_write_batch_json_content_is_valid(
        self, tmp_path: Path, sample_batch_result: BatchRefinementResult
    ) -> None:
        """出力されたJSONファイルの内容が正しいことをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"

        writer.write_batch(sample_batch_result, output_dir)

        json_files = list(output_dir.glob("*.json"))
        with json_files[0].open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_count"] == 1
        assert data["success_count"] == 1
        assert data["error_count"] == 0
        assert data["errors"] == []
        assert data["processing_time"] == 12.5
        assert data["results"][0]["final_metadata"]["title"] == "Test Movie"

    def test_write_batch_uses_timestamp_format(
        self, tmp_path: Path, sample_batch_result: BatchRefinementResult
    ) -> None:
        """write_batch()がタイムスタンプ付きのファイル名を使うことをテスト"""
        writer = RefinementResultWriter()
        output_dir = tmp_path / "output"

        with patch("movie_metadata.refinement_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 2, 7, 14, 30, 25)
            writer.write_batch(sample_batch_result, output_dir)

        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 1
        assert json_files[0].name == "batch_refinement_result_20260207_143025.json"
