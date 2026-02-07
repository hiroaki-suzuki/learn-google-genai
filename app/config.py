"""アプリケーション設定モジュール

環境変数とデフォルト値を使用してアプリケーション設定を管理します。
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(env_file=".env")

    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    csv_filename: str | None = Field(default=None, validation_alias="CSV_FILENAME")
    csv_path: Path = Field(default=Path("data/movies_test3.csv"))
    output_dir: Path = Field(default=Path("data/output"))
    model_name: str = Field(default="gemini-3-flash-preview")
    rate_limit_sleep: float = Field(default=1.0)
    log_level: str = Field(default="INFO")

    @field_validator("csv_path", mode="before")
    @classmethod
    def set_csv_path(cls, v: Path, info) -> Path:
        """CSV_FILENAMEが設定されている場合はそれを使用"""
        csv_filename = info.data.get("csv_filename")
        if csv_filename:
            return Path(f"data/{csv_filename}")
        return v if isinstance(v, Path) else Path(v)
