import logging

from google.genai import errors

from movie_metadata.genai_client import GenAIClient
from movie_metadata.models import MovieInput, MovieMetadata

logger = logging.getLogger(__name__)


def _build_input_info(movie_input: MovieInput) -> str:
    """MovieInputのフィールド情報をdescriptionを使って構築"""
    fields = MovieInput.model_fields
    lines = []
    for field_name, field_info in fields.items():
        value = getattr(movie_input, field_name)
        description = field_info.description or field_name
        lines.append(f"{description}: {value}")
    return "\n".join(lines)


def fetch_movie_metadata(
    movie_input: MovieInput,
    client: GenAIClient,
) -> MovieMetadata:
    """
    Google Search groundingで映画メタデータを取得

    Args:
        movie_input: 映画の基本情報
        client: GenAIClientインスタンス

    Returns:
        MovieMetadata: 取得したメタデータ

    Raises:
        errors.ClientError: クライアントエラー
        errors.ServerError: サーバーエラー
        errors.APIError: その他のAPIエラー
        Exception: 予期しないエラー
    """
    logger.info(f"Fetching metadata for: {movie_input.title}")

    # プロンプト作成（descriptionを活用）
    input_info = _build_input_info(movie_input)

    # NOTE: response_schemaのdescriptionがAPIに送信されるため、
    # プロンプト内で出力項目を明示的に列挙する必要はない
    prompt = f"""
# 映画メタデータ取得タスク

以下の映画について、最新の情報をGoogle Searchで検索し、詳細なメタデータを提供してください。

## 映画情報
{input_info}

## 情報収集の指針
- すべてのメタ情報は**日本語の情報を優先的に使用**してください
- 日本語の情報が見つからない場合のみ、英語など他の言語の情報を使用してください
- 人名や固有名詞は、可能な限り日本語表記（カタカナまたは漢字）で提供してください

## エラーハンドリング
- 情報が見つからない項目については「情報なし」と記載してください
- リスト形式の項目で情報がない場合は、空のリストを返してください
"""

    try:
        response_text = client.generate_content(
            prompt,
            response_schema=MovieMetadata,
            use_google_search=True,
        )

        # Pydanticモデルでパース
        metadata = MovieMetadata.model_validate_json(response_text)
        logger.info(f"Successfully fetched metadata for {movie_input.title}")
        return metadata

    except errors.ClientError as e:
        logger.error(f"Client error for {movie_input.title}: {e}")
        raise
    except errors.ServerError as e:
        logger.error(f"Server error for {movie_input.title}: {e}")
        raise
    except errors.APIError as e:
        logger.error(f"API error for {movie_input.title}: {e}")
        raise
    except ValueError as e:
        # 空のレスポンスの場合はデフォルト値で返す
        logger.warning(
            f"Returning default metadata for {movie_input.title} due to: {e}"
        )
        return MovieMetadata(
            title=movie_input.title,
            japanese_titles=["情報なし"],
            release_date=movie_input.release_date,
            country=movie_input.country,
            distributor="情報なし",
            box_office="情報なし",
            cast=["情報なし"],
            music=["情報なし"],
            voice_actors=["情報なし"],
        )
    except Exception:
        # 予期しないエラーの場合はログに記録して再送出
        logger.exception(f"Unexpected error for {movie_input.title}")
        raise
