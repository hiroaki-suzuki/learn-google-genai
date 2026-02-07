"""genai_clientモジュールのテスト"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from movie_metadata.genai_client import GenAIClient


class SampleSchema(BaseModel):
    name: str
    value: int


@pytest.fixture
def mock_genai_client() -> GenAIClient:
    """モック化されたGenAIClientを生成"""
    with patch("movie_metadata.genai_client.genai.Client"):
        client = GenAIClient(api_key="test-key", model_name="test-model")
    return client


class TestGenAIClientInit:
    """GenAIClient初期化のテスト"""

    def test_init_default_model(self) -> None:
        """デフォルトモデル名で初期化できるテスト"""
        with patch("movie_metadata.genai_client.genai.Client"):
            client = GenAIClient(api_key="test-key")
        assert client.model_name == "gemini-3-flash-preview"

    def test_init_custom_model(self) -> None:
        """カスタムモデル名で初期化できるテスト"""
        with patch("movie_metadata.genai_client.genai.Client"):
            client = GenAIClient(api_key="test-key", model_name="custom-model")
        assert client.model_name == "custom-model"

    def test_init_creates_genai_client(self) -> None:
        """内部のgenai.Clientが正しいAPIキーで生成されること"""
        with patch("movie_metadata.genai_client.genai.Client") as mock_cls:
            GenAIClient(api_key="my-secret-key")
        mock_cls.assert_called_once_with(api_key="my-secret-key")


class TestGenAIClientGenerateContent:
    """GenAIClient.generate_contentのテスト"""

    def test_generate_content_success(self, mock_genai_client: GenAIClient) -> None:
        """正常なコンテンツ生成テスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "Generated text"
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act
        result = mock_genai_client.generate_content("test prompt")

        # Assert
        assert result == "Generated text"
        mock_genai_client._client.models.generate_content.assert_called_once()  # type: ignore[possibly-missing-attribute]

    def test_generate_content_with_schema(self, mock_genai_client: GenAIClient) -> None:
        """スキーマ付きコンテンツ生成でJSON MIMEタイプが設定されるテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = '{"name": "test", "value": 42}'
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act
        result = mock_genai_client.generate_content(
            "test prompt", response_schema=SampleSchema
        )

        # Assert
        assert result == '{"name": "test", "value": 42}'
        call_kwargs = mock_genai_client._client.models.generate_content.call_args  # type: ignore[possibly-missing-attribute]
        config = call_kwargs.kwargs["config"]
        assert config.response_mime_type == "application/json"
        assert config.response_schema == SampleSchema

    def test_generate_content_without_schema_no_mime_type(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """スキーマ未指定時にresponse_mime_typeがNoneであるテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "plain text"
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.generate_content("test prompt")

        # Assert
        call_kwargs = mock_genai_client._client.models.generate_content.call_args  # type: ignore[possibly-missing-attribute]
        config = call_kwargs.kwargs["config"]
        assert config.response_mime_type is None
        assert config.response_schema is None

    def test_generate_content_with_google_search(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """Google Search有効時にツールが設定されるテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "Search result"
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act
        result = mock_genai_client.generate_content(
            "test prompt", use_google_search=True
        )

        # Assert
        assert result == "Search result"
        call_kwargs = mock_genai_client._client.models.generate_content.call_args  # type: ignore[possibly-missing-attribute]
        config = call_kwargs.kwargs["config"]
        assert len(config.tools) == 1

    def test_generate_content_without_google_search(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """Google Search無効時にツールが空であるテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "result"
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.generate_content("test prompt", use_google_search=False)

        # Assert
        call_kwargs = mock_genai_client._client.models.generate_content.call_args  # type: ignore[possibly-missing-attribute]
        config = call_kwargs.kwargs["config"]
        assert len(config.tools) == 0

    def test_generate_content_empty_response_raises(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """空レスポンス時にValueErrorが発生するテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = None
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act & Assert
        with pytest.raises(ValueError, match="API応答が空です"):
            mock_genai_client.generate_content("test prompt")

    def test_generate_content_passes_model_name(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """指定したモデル名がAPI呼び出しに渡されるテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "result"
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.generate_content("test prompt")

        # Assert
        call_kwargs = mock_genai_client._client.models.generate_content.call_args  # type: ignore[possibly-missing-attribute]
        assert call_kwargs.kwargs["model"] == "test-model"

    def test_generate_content_passes_prompt(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """プロンプトがAPI呼び出しに渡されるテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "result"
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.generate_content("my specific prompt")

        # Assert
        call_kwargs = mock_genai_client._client.models.generate_content.call_args  # type: ignore[possibly-missing-attribute]
        assert call_kwargs.kwargs["contents"] == "my specific prompt"


class TestGenAIClientContextManager:
    """GenAIClientコンテキストマネージャーのテスト"""

    def test_enter_returns_self(self, mock_genai_client: GenAIClient) -> None:
        """__enter__がselfを返すテスト"""
        # Act
        result = mock_genai_client.__enter__()

        # Assert
        assert result is mock_genai_client

    def test_exit_calls_close(self, mock_genai_client: GenAIClient) -> None:
        """__exit__がclose()を呼び出すテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock()  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.__exit__(None, None, None)

        # Assert
        mock_genai_client._client.close.assert_called_once()

    def test_with_statement_usage(self) -> None:
        """with文で正常に使用できるテスト"""
        # Arrange
        with patch("movie_metadata.genai_client.genai.Client") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            # Act
            with GenAIClient(api_key="test-key") as client:
                assert client is not None

            # Assert
            mock_instance.close.assert_called_once()

    def test_exit_calls_close_even_with_exception(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """例外発生時でもclose()が呼ばれるテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock()  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.__exit__(ValueError, ValueError("test"), None)

        # Assert
        mock_genai_client._client.close.assert_called_once()

    def test_close_delegates_to_internal_client(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """close()が内部clientのclose()を委譲するテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock()  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.close()

        # Assert
        mock_genai_client._client.close.assert_called_once()

    def test_close_suppresses_errors(self, mock_genai_client: GenAIClient) -> None:
        """close()のエラーが抑制されるテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock(  # type: ignore[invalid-assignment]
            side_effect=RuntimeError("close failed")
        )

        # Act & Assert - エラーが発生しないこと
        mock_genai_client.close()

    def test_close_can_be_called_multiple_times(
        self, mock_genai_client: GenAIClient
    ) -> None:
        """複数回close()を呼んでも安全であるテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock()  # type: ignore[invalid-assignment]

        # Act
        mock_genai_client.close()
        mock_genai_client.close()
        mock_genai_client.close()

        # Assert - 内部clientのclose()が3回呼ばれること
        assert mock_genai_client._client.close.call_count == 3


class TestGenAIClientLogging:
    """GenAIClientのログ出力テスト"""

    def test_init_logs_model_info(self, caplog: pytest.LogCaptureFixture) -> None:
        """初期化時にモデル名をログ出力するテスト"""
        # Arrange
        with (
            caplog.at_level(logging.INFO),
            patch("movie_metadata.genai_client.genai.Client"),
        ):
            # Act
            GenAIClient(api_key="test-key", model_name="custom-model")

        # Assert
        assert (
            "GenAIクライアントを初期化しました（モデル: custom-model）" in caplog.text
        )

    def test_enter_logs_context_entry(
        self, mock_genai_client: GenAIClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """コンテキストマネージャー開始時にログ出力するテスト"""
        # Arrange
        with caplog.at_level(logging.DEBUG):
            # Act
            mock_genai_client.__enter__()

        # Assert
        assert "GenAIクライアントのコンテキストマネージャーに入りました" in caplog.text

    def test_exit_logs_context_exit_without_exception(
        self, mock_genai_client: GenAIClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """例外なしでコンテキストマネージャー終了時にログ出力するテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock()  # type: ignore[invalid-assignment]
        with caplog.at_level(logging.DEBUG):
            # Act
            mock_genai_client.__exit__(None, None, None)

        # Assert
        assert (
            "GenAIクライアントのコンテキストマネージャーを終了します （例外: なし）"
            in caplog.text
        )

    def test_exit_logs_context_exit_with_exception(
        self, mock_genai_client: GenAIClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """例外ありでコンテキストマネージャー終了時にログ出力するテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock()  # type: ignore[invalid-assignment]
        with caplog.at_level(logging.DEBUG):
            # Act
            mock_genai_client.__exit__(ValueError, ValueError("test"), None)

        # Assert
        assert (
            "GenAIクライアントのコンテキストマネージャーを終了します （例外: あり）"
            in caplog.text
        )

    def test_close_logs_success(
        self, mock_genai_client: GenAIClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """close成功時にログ出力するテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock()  # type: ignore[invalid-assignment]
        with caplog.at_level(logging.INFO):
            # Act
            mock_genai_client.close()

        # Assert
        assert "GenAIクライアントを終了し、リソースを解放しています" in caplog.text

    def test_close_logs_error_on_failure(
        self, mock_genai_client: GenAIClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """close失敗時にエラーログを出力するテスト"""
        # Arrange
        mock_genai_client._client.close = MagicMock(  # type: ignore[invalid-assignment]
            side_effect=RuntimeError("close error")
        )
        with caplog.at_level(logging.WARNING):
            # Act
            mock_genai_client.close()

        # Assert
        assert "GenAIクライアントのクローズ中にエラーが発生しました" in caplog.text
        assert "close error" in caplog.text

    def test_generate_content_logs_generation_info(
        self, mock_genai_client: GenAIClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """generate_content呼び出し時にログ出力するテスト"""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "result"
        mock_genai_client._client.models.generate_content.return_value = mock_response  # type: ignore[invalid-assignment]
        with caplog.at_level(logging.DEBUG):
            # Act
            mock_genai_client.generate_content(
                "test prompt", response_schema=SampleSchema, use_google_search=True
            )

        # Assert
        assert "コンテンツを生成中（モデル: test-model" in caplog.text
        assert "検索: True" in caplog.text
        assert "SampleSchema" in caplog.text
