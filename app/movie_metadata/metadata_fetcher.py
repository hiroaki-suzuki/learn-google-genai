"""映画メタデータフェッチャーモジュール

Google Search groundingを使用して映画のメタデータを取得する機能を提供します。
"""

import logging

from google.genai import errors

from movie_metadata.genai_client import GenAIClient
from movie_metadata.models import MovieInput, MovieMetadata
from movie_metadata.prompts import build_metadata_fetch_prompt

logger = logging.getLogger(__name__)


class MovieMetadataFetcher:
    """映画メタデータフェッチャー

    Google Search groundingを使用して映画のメタデータを取得するクラスです。

    Args:
        client: GenAIClientインスタンス

    Examples:
        with GenAIClient(api_key="YOUR_KEY") as client:
            fetcher = MovieMetadataFetcher(client)
            movie_input = MovieInput(title="映画タイトル", ...)
            metadata = fetcher.fetch(movie_input)
    """

    def __init__(self, client: GenAIClient) -> None:
        self._client = client
        logger.debug("MovieMetadataFetcherを初期化しました")

    @staticmethod
    def _build_input_info(movie_input: MovieInput) -> str:
        """MovieInputのフィールド情報をdescriptionを使って構築

        Args:
            movie_input: 映画の基本情報

        Returns:
            フィールド情報の文字列
        """
        fields = MovieInput.model_fields
        lines = []
        for field_name, field_info in fields.items():
            value = getattr(movie_input, field_name)
            description = field_info.description or field_name
            lines.append(f"{description}: {value}")
        return "\n".join(lines)

    def _fetch_metadata(self, movie_input: MovieInput, prompt: str) -> MovieMetadata:
        """メタデータを取得する共通ロジック

        Args:
            movie_input: 映画の基本情報
            prompt: 取得用プロンプト

        Returns:
            取得したメタデータ

        Raises:
            errors.ClientError: クライアントエラー
            errors.ServerError: サーバーエラー
            errors.APIError: その他のAPIエラー
            Exception: 予期しないエラー
        """
        try:
            response_text = self._client.generate_content(
                prompt,
                response_schema=MovieMetadata,
                use_google_search=True,
            )

            # Pydanticモデルでパース
            metadata = MovieMetadata.model_validate_json(response_text)
            logger.info(f"{movie_input.title} のメタデータを取得しました")
            return metadata

        except errors.ClientError as e:
            logger.error(f"{movie_input.title} のクライアントエラー: {e}")
            raise
        except errors.ServerError as e:
            logger.error(f"{movie_input.title} のサーバーエラー: {e}")
            raise
        except errors.APIError as e:
            logger.error(f"{movie_input.title} のAPIエラー: {e}")
            raise
        except ValueError as e:
            # 空のレスポンスの場合はデフォルト値で返す
            warning_msg = f"{movie_input.title} のデフォルト値を返します（理由: {e}）"
            logger.warning(warning_msg)
            return MovieMetadata(
                title=movie_input.title,
                japanese_titles=["情報なし"],
                original_work="情報なし",
                original_authors=["情報なし"],
                release_date=movie_input.release_date,
                country=movie_input.country,
                distributor="情報なし",
                production_companies=["情報なし"],
                box_office="情報なし",
                cast=["情報なし"],
                screenwriters=["情報なし"],
                music=["情報なし"],
                voice_actors=["情報なし"],
            )
        except Exception:
            # 予期しないエラーの場合はログに記録して再送出
            logger.exception(f"{movie_input.title} の予期しないエラー")
            raise

    def fetch(self, movie_input: MovieInput) -> MovieMetadata:
        """映画のメタデータを取得

        Google Search groundingを使用して、映画の詳細なメタデータを取得します。

        Args:
            movie_input: 映画の基本情報

        Returns:
            取得したメタデータ

        Raises:
            errors.ClientError: クライアントエラー
            errors.ServerError: サーバーエラー
            errors.APIError: その他のAPIエラー
            Exception: 予期しないエラー
        """
        logger.info(f"メタデータを取得中: {movie_input.title}")

        # プロンプト作成（descriptionを活用）
        input_info = self._build_input_info(movie_input)
        prompt = build_metadata_fetch_prompt(input_info)

        return self._fetch_metadata(movie_input, prompt)

    def fetch_with_improvement(
        self, movie_input: MovieInput, improvement_instruction: str
    ) -> MovieMetadata:
        """改善指示に基づいてメタデータを再取得

        改善提案をプロンプトに組み込んでGoogle Searchで再検索します。

        Args:
            movie_input: 映画の基本情報
            improvement_instruction: 改善指示

        Returns:
            取得したメタデータ

        Raises:
            errors.ClientError: クライアントエラー
            errors.ServerError: サーバーエラー
            errors.APIError: その他のAPIエラー
            Exception: 予期しないエラー
        """
        logger.info(f"改善指示に基づいてメタデータを再取得中: {movie_input.title}")

        # プロンプト作成（改善指示を含む）
        input_info = self._build_input_info(movie_input)
        prompt = build_metadata_fetch_prompt(input_info, improvement_instruction)

        return self._fetch_metadata(movie_input, prompt)
