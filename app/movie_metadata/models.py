from pydantic import BaseModel, Field


class MovieInput(BaseModel):
    """CSV読み込み用の映画入力モデル"""

    title: str = Field(description="映画のタイトル")
    release_date: str = Field(description="公開日（YYYY-MM-DD形式）")
    country: str = Field(description="制作国")


class MovieMetadata(BaseModel):
    """LLM出力用の映画メタデータモデル"""

    title: str = Field(description="映画のタイトル")
    japanese_titles: list[str] = Field(
        description="日本語タイトルのリスト。正式名称、略称、別名など複数の呼び方がある場合はすべて含める。日本の作品の場合は原題を含む。情報が見つからない場合は空のリストまたは['情報なし']を返す。"
    )
    release_date: str = Field(description="公開日（YYYY-MM-DD形式）")
    country: str = Field(description="制作国")
    distributor: str = Field(
        description="配給会社。日本での配給会社を優先。情報が見つからない場合は「情報なし」と記載。"
    )
    box_office: str = Field(
        description=(
            "興行収入。世界興行収入または主要市場の興行収入。"
            "通貨単位を含む（例: $395 million）。"
            "情報が見つからない場合は「情報なし」と記載。"
        )
    )
    cast: list[str] = Field(
        description="主要な出演者のリスト（最大5名）。情報が見つからない場合は空のリストまたは['情報なし']を返す。"
    )
    music: list[str] = Field(
        description="楽曲または作曲家のリスト。主題歌や劇伴作曲家を含む。情報が見つからない場合は空のリストまたは['情報なし']を返す。"
    )
    voice_actors: list[str] = Field(
        description="声優のリスト。アニメの場合は日本語声優、実写の場合は日本語吹き替え声優。該当しない場合は空のリストまたは['情報なし']を返す。"
    )
