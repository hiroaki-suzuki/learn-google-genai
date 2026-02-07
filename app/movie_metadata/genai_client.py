"""Google GenAI APIクライアントモジュール

GenAI APIとの通信を管理する再利用可能なクライアントクラスを提供します。
"""

import logging
from collections.abc import Callable
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GenAIClient:
    """Google GenAI APIクライアント

    APIクライアントのライフサイクル管理とコンテンツ生成機能を提供します。

    Args:
        api_key: Google GenAI APIキー
        model_name: 使用するモデル名

    Examples:
        コンテキストマネージャーとして使用（推奨）:
            with GenAIClient(api_key="YOUR_KEY") as client:
                result = client.generate_content("Hello")

        明示的なclose()を使用:
            client = GenAIClient(api_key="YOUR_KEY")
            try:
                result = client.generate_content("Hello")
            finally:
                client.close()
    """

    def __init__(
        self, api_key: str, model_name: str = "gemini-3-flash-preview"
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name
        logger.info(f"GenAIクライアントを初期化しました（モデル: {model_name}）")

    def __enter__(self) -> GenAIClient:
        """コンテキストマネージャーのエントリーポイント"""
        logger.debug("GenAIクライアントのコンテキストマネージャーに入りました")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """コンテキストマネージャーの終了処理"""
        logger.debug(
            f"GenAIクライアントのコンテキストマネージャーを終了します "
            f"（例外: {'あり' if exc_type else 'なし'}）"
        )
        self.close()

    def close(self) -> None:
        """クライアントをクローズし、リソースを解放"""
        try:
            logger.info("GenAIクライアントを終了し、リソースを解放しています")
            self._client.close()
        except Exception as e:
            logger.warning(f"GenAIクライアントのクローズ中にエラーが発生しました: {e}")

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_content(
        self,
        prompt: str,
        *,
        response_schema: type[BaseModel] | None = None,
        use_google_search: bool = False,
    ) -> str:
        """コンテンツを生成する

        Args:
            prompt: 生成プロンプト
            response_schema: レスポンスのPydanticスキーマ（JSON出力時）
            use_google_search: Google Search groundingを使用するか

        Returns:
            生成されたテキスト

        Raises:
            google.genai.errors.ClientError: クライアントエラー
            google.genai.errors.ServerError: サーバーエラー
            google.genai.errors.APIError: その他のAPIエラー
            ValueError: レスポンスが空の場合
        """
        tools: list[types.Tool | Callable[..., Any]] = []
        if use_google_search:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        config = types.GenerateContentConfig(
            tools=tools,
            response_mime_type="application/json" if response_schema else None,
            response_schema=response_schema,
        )

        logger.debug(
            f"コンテンツを生成中（モデル: {self._model_name}, "
            f"検索: {use_google_search}, スキーマ: {response_schema}）"
        )

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=config,
        )

        if response.text is None:
            raise ValueError("API応答が空です")

        return response.text
