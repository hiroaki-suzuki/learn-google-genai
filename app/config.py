"""アプリケーション設定モジュール

環境変数とデフォルト値を使用してアプリケーション設定を管理します。
"""

import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> str:
    """ENV環境変数に基づいて適切な環境変数ファイルパスを返す

    Returns:
        str: 環境変数ファイルのパス

    Raises:
        FileNotFoundError: 環境変数ファイルが存在しない場合
    """
    env = os.getenv("ENV", "production")

    env_file = ".env.test" if env == "test" else ".env"

    env_path = Path(env_file)
    if not env_path.exists():
        raise FileNotFoundError(
            f"環境変数ファイル '{env_file}' が見つかりません。"
            f"ENV={env} に対応するファイルを作成してください。"
        )

    return env_file


class AppConfig(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(env_file=get_env_file())

    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    csv_filename: str | None = Field(default=None, validation_alias="CSV_FILENAME")
    csv_path: Path = Field(default=Path("data/movies_test3.csv"))
    output_dir: Path = Field(default=Path("data/output"))
    model_name: str = Field(default="gemini-3-flash-preview")
    rate_limit_sleep: float = Field(default=1.0)
    log_level: str = Field(default="INFO")
    quality_score_threshold: float = Field(
        default=0.8, validation_alias="QUALITY_SCORE_THRESHOLD"
    )

    @field_validator("csv_path", mode="before")
    @classmethod
    def set_csv_path(cls, v: Path, info) -> Path:
        """CSV_FILENAMEが設定されている場合はそれを使用"""
        csv_filename = info.data.get("csv_filename")
        if csv_filename:
            return Path(f"data/{csv_filename}")
        return v if isinstance(v, Path) else Path(v)
