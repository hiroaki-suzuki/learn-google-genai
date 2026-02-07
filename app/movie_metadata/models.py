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


# ========================================
# メタデータ品質評価・改善ループ用モデル
# ========================================


class MetadataFieldScore(BaseModel):
    """メタデータフィールドの評価スコア"""

    field_name: str = Field(description="評価対象のフィールド名")
    score: float = Field(description="0.0〜5.0のスコア", ge=0.0, le=5.0)
    reasoning: str = Field(description="このスコアをつけた理由")


class MetadataEvaluationResult(BaseModel):
    """メタデータ評価結果"""

    iteration: int = Field(description="イテレーション番号（1から開始）")
    field_scores: list[MetadataFieldScore] = Field(description="各フィールドのスコア")
    overall_status: str = Field(
        description=(
            "全体のステータス（'pass': すべて3.5以上, 'fail': 1つ以上が3.5未満）"
        )
    )
    improvement_suggestions: str = Field(
        description="改善提案（スコアが3.5未満のフィールドに対する具体的な提案）"
    )


class RefinementHistoryEntry(BaseModel):
    """改善履歴のエントリ"""

    iteration: int = Field(description="イテレーション番号")
    metadata: MovieMetadata = Field(description="このイテレーションのメタデータ")
    evaluation: MetadataEvaluationResult = Field(
        description="このイテレーションの評価結果"
    )


class MetadataRefinementResult(BaseModel):
    """メタデータ改善プロセスの最終結果"""

    final_metadata: MovieMetadata = Field(description="最終的なメタデータ")
    history: list[RefinementHistoryEntry] = Field(description="全イテレーションの履歴")
    success: bool = Field(description="すべてのフィールドが閾値3.5以上を達成したか")
    total_iterations: int = Field(description="実行したイテレーション数")


class MetadataEvaluationOutput(BaseModel):
    """メタデータ評価用のLLM出力スキーマ"""

    field_scores: list[MetadataFieldScore] = Field(description="各フィールドのスコア")
    improvement_suggestions: str = Field(
        description="改善提案（スコアが3.5未満のフィールドに対する具体的な提案。すべて3.5以上なら'なし'）"
    )
