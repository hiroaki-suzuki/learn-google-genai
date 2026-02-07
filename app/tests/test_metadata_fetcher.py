"""MovieMetadataFetcherの単体テスト"""

from unittest.mock import MagicMock

import pytest
from google.genai import errors

from movie_metadata.metadata_fetcher import MovieMetadataFetcher
from movie_metadata.models import MovieInput, MovieMetadata


class TestMovieMetadataFetcher:
    """MovieMetadataFetcherクラスのテスト"""

    def test_init(self, mock_genai_client: MagicMock) -> None:
        """初期化テスト"""
        fetcher = MovieMetadataFetcher(mock_genai_client)
        assert fetcher._client == mock_genai_client

    def test_build_input_info(self, sample_movie_input: MovieInput) -> None:
        """_build_input_infoメソッドのテスト"""
        info = MovieMetadataFetcher._build_input_info(sample_movie_input)
        assert "映画のタイトル: Test Movie" in info
        assert "公開日（YYYY-MM-DD形式）: 2024-01-01" in info
        assert "制作国: Japan" in info

    def test_fetch_success(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
        sample_metadata_json: str,
    ) -> None:
        """fetchメソッドの正常系テスト"""
        # モックの設定
        mock_genai_client.generate_content.return_value = sample_metadata_json

        fetcher = MovieMetadataFetcher(mock_genai_client)
        result = fetcher.fetch(sample_movie_input)

        # 結果の検証
        assert isinstance(result, MovieMetadata)
        assert result.title == "Test Movie"
        assert result.japanese_titles == ["テスト映画"]

        # generate_contentが適切な引数で呼ばれたか確認
        mock_genai_client.generate_content.assert_called_once()
        call_args = mock_genai_client.generate_content.call_args
        assert call_args.kwargs["response_schema"] == MovieMetadata
        assert call_args.kwargs["use_google_search"] is True

    def test_fetch_with_improvement_success(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
        sample_metadata_json: str,
    ) -> None:
        """fetch_with_improvementメソッドの正常系テスト"""
        # モックの設定
        mock_genai_client.generate_content.return_value = sample_metadata_json
        improvement_instruction = "配給会社の情報をより詳細に記載してください"

        fetcher = MovieMetadataFetcher(mock_genai_client)
        result = fetcher.fetch_with_improvement(
            sample_movie_input, improvement_instruction
        )

        # 結果の検証
        assert isinstance(result, MovieMetadata)
        assert result.title == "Test Movie"

        # generate_contentが適切な引数で呼ばれたか確認
        mock_genai_client.generate_content.assert_called_once()
        call_args = mock_genai_client.generate_content.call_args
        prompt = call_args.args[0]
        assert improvement_instruction in prompt

    def test_fetch_client_error(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
    ) -> None:
        """fetchメソッドのClientErrorテスト"""
        # ClientErrorをモック
        mock_genai_client.generate_content.side_effect = errors.ClientError(
            code=400, response_json={"error": {"message": "Client error"}}
        )

        fetcher = MovieMetadataFetcher(mock_genai_client)
        with pytest.raises(errors.ClientError):
            fetcher.fetch(sample_movie_input)

    def test_fetch_server_error(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
    ) -> None:
        """fetchメソッドのServerErrorテスト"""
        # ServerErrorをモック
        mock_genai_client.generate_content.side_effect = errors.ServerError(
            code=500, response_json={"error": {"message": "Server error"}}
        )

        fetcher = MovieMetadataFetcher(mock_genai_client)
        with pytest.raises(errors.ServerError):
            fetcher.fetch(sample_movie_input)

    def test_fetch_api_error(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
    ) -> None:
        """fetchメソッドのAPIErrorテスト"""
        # APIErrorをモック
        mock_genai_client.generate_content.side_effect = errors.APIError(
            code=429, response_json={"error": {"message": "API error"}}
        )

        fetcher = MovieMetadataFetcher(mock_genai_client)
        with pytest.raises(errors.APIError):
            fetcher.fetch(sample_movie_input)

    def test_fetch_value_error_returns_default(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
    ) -> None:
        """fetchメソッドのValueError時にデフォルト値を返すテスト"""
        # 空のレスポンスでValueErrorを発生させる
        mock_genai_client.generate_content.return_value = ""

        fetcher = MovieMetadataFetcher(mock_genai_client)
        result = fetcher.fetch(sample_movie_input)

        # デフォルト値の検証
        assert isinstance(result, MovieMetadata)
        assert result.title == sample_movie_input.title
        assert result.japanese_titles == ["情報なし"]
        assert result.release_date == sample_movie_input.release_date
        assert result.country == sample_movie_input.country
        assert result.distributor == "情報なし"
        assert result.box_office == "情報なし"
        assert result.cast == ["情報なし"]
        assert result.music == ["情報なし"]
        assert result.voice_actors == ["情報なし"]

    def test_fetch_unexpected_error(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
    ) -> None:
        """fetchメソッドの予期しないエラー時に再送出するテスト"""
        # 予期しないエラーをモック
        mock_genai_client.generate_content.side_effect = RuntimeError(
            "Unexpected error"
        )

        fetcher = MovieMetadataFetcher(mock_genai_client)
        with pytest.raises(RuntimeError):
            fetcher.fetch(sample_movie_input)

    def test_fetch_with_improvement_client_error(
        self,
        mock_genai_client: MagicMock,
        sample_movie_input: MovieInput,
    ) -> None:
        """fetch_with_improvementメソッドのClientErrorテスト"""
        # ClientErrorをモック
        mock_genai_client.generate_content.side_effect = errors.ClientError(
            code=400, response_json={"error": {"message": "Client error"}}
        )

        fetcher = MovieMetadataFetcher(mock_genai_client)
        with pytest.raises(errors.ClientError):
            fetcher.fetch_with_improvement(sample_movie_input, "改善指示")
