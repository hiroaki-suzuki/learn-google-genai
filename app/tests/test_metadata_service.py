"""metadata_serviceモジュールのテスト"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from movie_metadata.csv_reader import CSVReader
from movie_metadata.genai_client import GenAIClient
from movie_metadata.json_writer import JSONWriter
from movie_metadata.metadata_service import MetadataService
from movie_metadata.models import MovieInput, MovieMetadata


@pytest.fixture
def mock_client() -> MagicMock:
    """モック化されたGenAIClient"""
    return MagicMock(spec=GenAIClient)


@pytest.fixture
def mock_csv_reader() -> MagicMock:
    """モック化されたCSVReader"""
    return MagicMock(spec=CSVReader)


@pytest.fixture
def mock_json_writer() -> MagicMock:
    """モック化されたJSONWriter"""
    return MagicMock(spec=JSONWriter)


@pytest.fixture
def service(
    mock_client: MagicMock,
    mock_csv_reader: MagicMock,
    mock_json_writer: MagicMock,
) -> MetadataService:
    """テスト用MetadataService"""
    return MetadataService(
        client=mock_client,
        csv_reader=mock_csv_reader,
        json_writer=mock_json_writer,
        rate_limit_sleep=0,  # テスト時は待機しない
    )


@pytest.fixture
def sample_movies() -> list[MovieInput]:
    """テスト用映画リスト"""
    return [
        MovieInput(title="Movie 1", release_date="2024-01-01", country="Japan"),
        MovieInput(title="Movie 2", release_date="2024-02-01", country="USA"),
    ]


@pytest.fixture
def sample_metadata_list() -> list[MovieMetadata]:
    """テスト用メタデータリスト"""
    return [
        MovieMetadata(
            title="Movie 1",
            japanese_titles=["映画1"],
            original_work="原作1",
            original_authors=["原作者1"],
            release_date="2024-01-01",
            country="Japan",
            distributor="配給社",
            production_companies=["制作会社1"],
            box_office="$1M",
            cast=["俳優"],
            screenwriters=["脚本家1"],
            music=["作曲家"],
            voice_actors=["声優"],
        ),
        MovieMetadata(
            title="Movie 2",
            japanese_titles=["映画2"],
            original_work="オリジナル",
            original_authors=[],
            release_date="2024-02-01",
            country="USA",
            distributor="Distributor",
            production_companies=["Production Co"],
            box_office="$2M",
            cast=["Actor"],
            screenwriters=["Writer"],
            music=["Composer"],
            voice_actors=["VA"],
        ),
    ]


class TestMetadataServiceProcess:
    """MetadataService.processのテスト"""

    def test_process_success(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        sample_movies: list[MovieInput],
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
    ) -> None:
        """正常な処理フローのテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with patch.object(service._fetcher, "fetch", side_effect=sample_metadata_list):
            # Act
            result = service.process(csv_path, output_dir)

        # Assert
        assert result["total"] == 2
        assert result["success"] == 2
        assert result["failed"] == 0
        mock_csv_reader.read.assert_called_once_with(csv_path)
        mock_json_writer.write.assert_called_once()

    def test_process_with_partial_failure(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        sample_movies: list[MovieInput],
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
    ) -> None:
        """一部の映画でエラーが発生するテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with patch.object(
            service._fetcher,
            "fetch",
            side_effect=[sample_metadata_list[0], RuntimeError("API error")],
        ):
            # Act
            result = service.process(csv_path, output_dir)

        # Assert
        assert result["total"] == 2
        assert result["success"] == 1
        assert result["failed"] == 1
        mock_json_writer.write.assert_called_once()

    def test_process_all_failures(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        sample_movies: list[MovieInput],
        tmp_path: Path,
    ) -> None:
        """全映画でエラーが発生するテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with patch.object(
            service._fetcher, "fetch", side_effect=RuntimeError("API error")
        ):
            # Act
            result = service.process(csv_path, output_dir)

        # Assert
        assert result["total"] == 2
        assert result["success"] == 0
        assert result["failed"] == 2
        mock_json_writer.write.assert_not_called()

    def test_process_empty_csv(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        tmp_path: Path,
    ) -> None:
        """空のCSVの場合のテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = []

        # Act
        result = service.process(csv_path, output_dir)

        # Assert
        assert result["total"] == 0
        assert result["success"] == 0
        assert result["failed"] == 0
        mock_json_writer.write.assert_not_called()

    def test_process_creates_output_dir(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        tmp_path: Path,
    ) -> None:
        """出力ディレクトリが作成されることのテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "nested" / "output"
        mock_csv_reader.read.return_value = []

        # Act
        service.process(csv_path, output_dir)

        # Assert
        assert output_dir.exists()

    def test_process_passes_movie_to_fetch(
        self,
        mock_client: MagicMock,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        tmp_path: Path,
    ) -> None:
        """fetcherのfetchメソッドにmovieが正しく渡されるテスト"""
        # Arrange
        service = MetadataService(
            client=mock_client,
            csv_reader=mock_csv_reader,
            json_writer=mock_json_writer,
            rate_limit_sleep=0,
        )
        movie = MovieInput(title="Test", release_date="2024-01-01", country="Japan")
        mock_csv_reader.read.return_value = [movie]
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"

        metadata = MovieMetadata(
            title="Test",
            japanese_titles=["テスト"],
            original_work="原作",
            original_authors=["原作者"],
            release_date="2024-01-01",
            country="Japan",
            distributor="配給",
            production_companies=["制作会社"],
            box_office="$1M",
            cast=["俳優"],
            screenwriters=["脚本家"],
            music=["作曲家"],
            voice_actors=["声優"],
        )

        with patch.object(
            service._fetcher, "fetch", return_value=metadata
        ) as mock_fetch:
            # Act
            service.process(csv_path, output_dir)

            # Assert
            mock_fetch.assert_called_once_with(movie)

    def test_process_output_json_filename_has_timestamp(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        sample_movies: list[MovieInput],
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
    ) -> None:
        """出力JSONファイル名にタイムスタンプが含まれるテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with (
            patch.object(service._fetcher, "fetch", side_effect=sample_metadata_list),
            patch("movie_metadata.metadata_service.datetime") as mock_datetime,
        ):
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            # Act
            service.process(csv_path, output_dir)

        # Assert
        write_call = mock_json_writer.write.call_args
        output_path = write_call.args[1]
        assert output_path.name == "movie_metadata_20240101_120000.json"

    def test_process_rate_limit_sleep(
        self,
        mock_client: MagicMock,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
    ) -> None:
        """レート制限の待機が正しく行われるテスト"""
        # Arrange
        service = MetadataService(
            client=mock_client,
            csv_reader=mock_csv_reader,
            json_writer=mock_json_writer,
            rate_limit_sleep=0.5,
        )
        movies = [
            MovieInput(title=f"Movie {i}", release_date="2024-01-01", country="Japan")
            for i in range(3)
        ]
        mock_csv_reader.read.return_value = movies
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"

        with (
            patch.object(
                service._fetcher,
                "fetch",
                side_effect=sample_metadata_list + [sample_metadata_list[0]],
            ),
            patch("movie_metadata.metadata_service.time.sleep") as mock_sleep,
        ):
            # Act
            service.process(csv_path, output_dir)

        # Assert: 3件中、最後の1件以外で待機 = 2回呼ばれる
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(0.5), call(0.5)])

    def test_process_no_sleep_after_last_movie(
        self,
        mock_client: MagicMock,
        mock_csv_reader: MagicMock,
        mock_json_writer: MagicMock,
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
    ) -> None:
        """最後の映画の後はスリープしないテスト"""
        # Arrange
        service = MetadataService(
            client=mock_client,
            csv_reader=mock_csv_reader,
            json_writer=mock_json_writer,
            rate_limit_sleep=1.0,
        )
        movies = [
            MovieInput(title="Only Movie", release_date="2024-01-01", country="Japan")
        ]
        mock_csv_reader.read.return_value = movies
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"

        with (
            patch.object(
                service._fetcher, "fetch", return_value=sample_metadata_list[0]
            ),
            patch("movie_metadata.metadata_service.time.sleep") as mock_sleep,
        ):
            # Act
            service.process(csv_path, output_dir)

        # Assert: 1件のみなのでスリープなし
        mock_sleep.assert_not_called()

    def test_process_csv_reader_error_propagates(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        tmp_path: Path,
    ) -> None:
        """CSVReader読み込みエラーが伝播するテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.side_effect = FileNotFoundError("Not found")

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Not found"):
            service.process(csv_path, output_dir)


class TestMetadataServiceLogging:
    """MetadataServiceのログ出力テスト"""

    def test_process_logs_csv_read_count(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        sample_movies: list[MovieInput],
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """CSVから読み込んだ映画の件数をログ出力するテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with (
            caplog.at_level(logging.INFO),
            patch.object(service._fetcher, "fetch", side_effect=sample_metadata_list),
        ):
            # Act
            service.process(csv_path, output_dir)

        # Assert
        assert "CSVから 2 件の映画を読み込みました" in caplog.text

    def test_process_logs_progress(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        sample_movies: list[MovieInput],
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """処理中の映画の進捗をログ出力するテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with (
            caplog.at_level(logging.INFO),
            patch.object(service._fetcher, "fetch", side_effect=sample_metadata_list),
        ):
            # Act
            service.process(csv_path, output_dir)

        # Assert
        assert "処理中 [1/2]: Movie 1" in caplog.text
        assert "処理中 [2/2]: Movie 2" in caplog.text

    def test_process_logs_completion_summary(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        sample_movies: list[MovieInput],
        sample_metadata_list: list[MovieMetadata],
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """処理完了時のサマリーをログ出力するテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with (
            caplog.at_level(logging.INFO),
            patch.object(service._fetcher, "fetch", side_effect=sample_metadata_list),
        ):
            # Act
            service.process(csv_path, output_dir)

        # Assert
        assert "=== 完了: 2/2件成功, 0件失敗 ===" in caplog.text

    def test_process_logs_fetch_error(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        sample_movies: list[MovieInput],
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """メタデータ取得失敗時にエラーログを出力するテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = [sample_movies[0]]

        with (
            caplog.at_level(logging.ERROR),
            patch.object(
                service._fetcher, "fetch", side_effect=RuntimeError("API error")
            ),
        ):
            # Act
            service.process(csv_path, output_dir)

        # Assert
        assert "Movie 1 のメタデータ取得に失敗しました" in caplog.text
        assert "API error" in caplog.text

    def test_process_logs_no_metadata_error(
        self,
        service: MetadataService,
        mock_csv_reader: MagicMock,
        sample_movies: list[MovieInput],
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """すべての取得が失敗した場合のエラーログテスト"""
        # Arrange
        csv_path = tmp_path / "test.csv"
        csv_path.touch()
        output_dir = tmp_path / "output"
        mock_csv_reader.read.return_value = sample_movies

        with (
            caplog.at_level(logging.ERROR),
            patch.object(
                service._fetcher, "fetch", side_effect=RuntimeError("API error")
            ),
        ):
            # Act
            service.process(csv_path, output_dir)

        # Assert
        assert "エラー: メタデータを取得できませんでした" in caplog.text
