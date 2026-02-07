"""アプリケーション設定モジュール

環境変数とデフォルト値を使用してアプリケーション設定を管理します。
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(env_file=".env")

    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    csv_path: Path = Field(default=Path("data/movies_test.csv"))
    output_dir: Path = Field(default=Path("data/output"))
    model_name: str = Field(default="gemini-3-flash-preview")
    rate_limit_sleep: float = Field(default=1.0)
    log_level: str = Field(default="INFO")
