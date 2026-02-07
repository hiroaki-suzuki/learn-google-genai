"""ロギング設定モジュール

構造化ログを提供し、本番環境での運用性を向上させます。
"""

import logging
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Path | None = None) -> None:
    """ロギング設定を初期化

    Args:
        level: ログレベル (DEBUG/INFO/WARNING/ERROR)
        log_file: ログファイルパス (オプション)
    """
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

    # サードパーティライブラリのログレベルを制限
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
