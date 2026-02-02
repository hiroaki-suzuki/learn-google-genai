from google import genai
from google.genai import types

from movie_metadata.models import MovieInput, MovieMetadata


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
    api_key: str,
) -> MovieMetadata:
    """
    Google Search groundingで映画メタデータを取得

    Args:
        movie_input: 映画の基本情報
        api_key: Google GenAI APIキー

    Returns:
        MovieMetadata: 取得したメタデータ

    Raises:
        Exception: API呼び出しまたはパースに失敗した場合
    """
    client = genai.Client(api_key=api_key)

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
        # API呼び出し
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                response_schema=MovieMetadata,
            ),
        )

        # Pydanticモデルでパース
        if response.text is None:
            raise ValueError("API応答が空です")
        metadata = MovieMetadata.model_validate_json(response.text)
        return metadata

    except Exception as e:
        # エラーが発生した場合はデフォルト値で返す
        print(f"  警告: メタデータ取得に失敗しました ({type(e).__name__}: {e})")
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
