"""config.pyのテストモジュール"""

from pathlib import Path
from unittest.mock import patch

from config import AppConfig


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

    def test_csv_filename_is_none_when_not_set(self) -> None:
        """CSV_FILENAMEが設定されていない場合、csv_filenameはNoneであるテスト"""
        # Arrange & Act
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            config = AppConfig()

        # Assert
        assert config.csv_filename is None
