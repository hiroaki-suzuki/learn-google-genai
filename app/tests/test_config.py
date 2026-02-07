"""config.pyのテストモジュール"""

from pathlib import Path
from unittest.mock import patch

import pytest

from config import AppConfig, get_env_file


class TestAppConfigCSVPath:
    """AppConfig.csv_pathのテストクラス"""

    def test_csv_path_default_when_csv_filename_not_set(self) -> None:
        """CSV_FILENAMEが設定されていない場合、デフォルト値を使用するテスト"""
        # Arrange & Act
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            config = AppConfig()

        # Assert
        assert config.csv_path == Path("data/movies_test3.csv")

    def test_csv_path_uses_csv_filename_when_set(self) -> None:
        """CSV_FILENAMEが設定されている場合、それを使用するテスト"""
        # Arrange & Act
        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key", "CSV_FILENAME": "movies.csv"},
            clear=True,
        ):
            config = AppConfig()

        # Assert
        assert config.csv_path == Path("data/movies.csv")

    def test_csv_path_prepends_data_directory(self) -> None:
        """CSV_FILENAMEにdataディレクトリが自動的に追加されるテスト"""
        # Arrange & Act
        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key", "CSV_FILENAME": "custom_movies.csv"},
            clear=True,
        ):
            config = AppConfig()

        # Assert
        assert config.csv_path == Path("data/custom_movies.csv")
        assert str(config.csv_path).startswith("data/")

    def test_csv_filename_field_exists(self) -> None:
        """csv_filenameフィールドが存在することを確認するテスト"""
        # Arrange & Act
        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key", "CSV_FILENAME": "test.csv"},
            clear=True,
        ):
            config = AppConfig()

        # Assert
        assert hasattr(config, "csv_filename")
        assert config.csv_filename == "test.csv"

    def test_csv_filename_is_none_when_not_set(self, tmp_path: Path) -> None:
        """CSV_FILENAMEが設定されていない場合、csv_filenameはNoneであるテスト"""
        # Arrange - CSV_FILENAMEを含まない一時的な.envファイルを作成
        test_env_file = tmp_path / ".env.test_custom"
        test_env_file.write_text("GEMINI_API_KEY=test-key\n")

        # Act - _env_fileパラメータで明示的に環境ファイルを指定
        # 型チェッカーは_env_fileを認識しないが、実行時には正常に動作する
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            config = AppConfig(_env_file=str(test_env_file))  # type: ignore[call-arg]

        # Assert
        assert config.csv_filename is None


class TestGetEnvFile:
    """get_env_file関数のテストクラス"""

    def test_returns_env_test_when_env_is_test(self, tmp_path: Path) -> None:
        """ENV=testの場合、.env.testを返すテスト"""
        # Arrange
        env_test_file = tmp_path / ".env.test"
        env_test_file.write_text("TEST=true")

        # Act & Assert
        with (
            patch.dict("os.environ", {"ENV": "test"}, clear=True),
            patch("config.Path") as mock_path,
        ):
            mock_path.return_value.exists.return_value = True
            result = get_env_file()
            assert result == ".env.test"

    def test_returns_env_when_env_is_production(self, tmp_path: Path) -> None:
        """ENV=productionの場合、.envを返すテスト"""
        # Arrange
        env_file = tmp_path / ".env"
        env_file.write_text("PRODUCTION=true")

        # Act & Assert
        with (
            patch.dict("os.environ", {"ENV": "production"}, clear=True),
            patch("config.Path") as mock_path,
        ):
            mock_path.return_value.exists.return_value = True
            result = get_env_file()
            assert result == ".env"

    def test_returns_env_when_env_not_set(self, tmp_path: Path) -> None:
        """ENV未設定の場合、.envを返すテスト（デフォルト値）"""
        # Arrange
        env_file = tmp_path / ".env"
        env_file.write_text("DEFAULT=true")

        # Act & Assert
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("config.Path") as mock_path,
        ):
            mock_path.return_value.exists.return_value = True
            result = get_env_file()
            assert result == ".env"

    def test_raises_file_not_found_error_when_env_file_missing(
        self,
    ) -> None:
        """環境変数ファイルが存在しない場合、FileNotFoundErrorを発生させるテスト"""
        # Act & Assert
        with (
            patch.dict("os.environ", {"ENV": "test"}, clear=True),
            patch("config.Path") as mock_path,
        ):
            mock_path.return_value.exists.return_value = False
            with pytest.raises(FileNotFoundError) as exc_info:
                get_env_file()

            assert ".env.test" in str(exc_info.value)
            assert "見つかりません" in str(exc_info.value)
