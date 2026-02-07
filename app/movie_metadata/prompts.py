"""メタデータ評価用のプロンプトテンプレート"""

from movie_metadata.models import (
    MetadataEvaluationResult,
    MovieInput,
    MovieMetadata,
)

# ========================================
# メタデータ評価用プロンプト
# ========================================

METADATA_EVALUATION_PROMPT_TEMPLATE = """
# 役割: 映画メタデータ品質評価者

あなたは、映画メタデータの品質を客観的に評価する専門家です。

## 評価対象の映画

**タイトル**: {title}
**公開日**: {release_date}
**制作国**: {country}

## メタデータ

### 1. japanese_titles (日本語タイトル)
{japanese_titles}

### 2. distributor (配給会社)
{distributor}

### 3. box_office (興行収入)
{box_office}

### 4. cast (主要な出演者)
{cast}

### 5. music (楽曲または作曲家)
{music}

### 6. voice_actors (声優)
{voice_actors}

## 評価基準

以下の6つのフィールドについて、それぞれ0.0〜5.0のスコアで評価してください。

### 評価観点

各フィールドは以下の3つの観点で評価してください：

1. **完全性 (Completeness)**: 情報が十分に含まれているか
   - 5.0点: 完全で詳細な情報が含まれている
   - 3.5点: 基本的な情報はあるが、一部不足している
   - 2.0点: 情報が大幅に不足している
   - 0.0点: 情報が全くない、または「情報なし」と記載されている

2. **正確性 (Accuracy)**: 情報が正確で信頼できるか
   - 5.0点: 明らかに正確で、詳細度が高い
   - 3.5点: 概ね正確だが、曖昧な部分がある
   - 2.0点: 不正確または疑わしい情報を含む
   - 0.0点: 明らかに誤っている

3. **有用性 (Usefulness)**: 情報が有用で価値があるか
   - 5.0点: 非常に有用で、詳細な情報を提供している
   - 3.5点: 基本的に有用だが、追加情報があればより良い
   - 2.0点: 限定的な有用性
   - 0.0点: 全く有用でない

### フィールド別の評価ポイント

- **japanese_titles**: 正式名称、略称、別名など複数の呼び方が含まれているか
- **distributor**: 日本での配給会社が明記されているか
- **box_office**: 通貨単位を含む具体的な金額が記載されているか
- **cast**: 主要な出演者が適切な人数（最大5名程度）リストされているか
- **music**: 主題歌や劇伴作曲家など、具体的な楽曲情報が含まれているか
- **voice_actors**: アニメの場合は日本語声優、実写の場合は
  吹き替え声優が適切にリストされているか

## 閾値

**合格基準**: すべてのフィールドが3.5以上

## 出力形式

各フィールドのスコアと理由、および改善提案を提供してください。
- スコアが3.5未満のフィールドについては、具体的な改善提案を含めてください
- すべてのフィールドが3.5以上の場合、improvement_suggestionsは「なし」としてください
"""


def build_metadata_evaluation_prompt(
    title: str,
    release_date: str,
    country: str,
    japanese_titles: list[str],
    distributor: str,
    box_office: str,
    cast: list[str],
    music: list[str],
    voice_actors: list[str],
) -> str:
    """メタデータ評価用プロンプトを構築

    Args:
        title: 映画タイトル
        release_date: 公開日
        country: 制作国
        japanese_titles: 日本語タイトルのリスト
        distributor: 配給会社
        box_office: 興行収入
        cast: 主要な出演者のリスト
        music: 楽曲または作曲家のリスト
        voice_actors: 声優のリスト

    Returns:
        構築されたプロンプト
    """

    def format_list(items: list[str]) -> str:
        """リストを読みやすい文字列に変換"""
        if not items or items == ["情報なし"]:
            return "情報なし"
        return "\n".join(f"  - {item}" for item in items)

    return METADATA_EVALUATION_PROMPT_TEMPLATE.format(
        title=title,
        release_date=release_date,
        country=country,
        japanese_titles=format_list(japanese_titles),
        distributor=distributor,
        box_office=box_office,
        cast=format_list(cast),
        music=format_list(music),
        voice_actors=format_list(voice_actors),
    )


# ========================================
# メタデータ改善提案用プロンプト
# ========================================

IMPROVEMENT_PROPOSAL_PROMPT_TEMPLATE = """
# 役割: 映画メタデータ改善提案者

あなたは、映画メタデータの品質を改善するための具体的な提案を行う専門家です。

## 対象の映画

**タイトル**: {title}
**公開日**: {release_date}
**制作国**: {country}

## 現在のメタデータ

### 1. japanese_titles (日本語タイトル)
{japanese_titles}

### 2. distributor (配給会社)
{distributor}

### 3. box_office (興行収入)
{box_office}

### 4. cast (主要な出演者)
{cast}

### 5. music (楽曲または作曲家)
{music}

### 6. voice_actors (声優)
{voice_actors}

## 評価結果

{evaluation_summary}

## タスク

スコアが3.5未満のフィールドについて、以下の形式で改善提案を生成してください：

1. **検索クエリの変更案**: より良い情報を得るための具体的な検索キーワード
2. **情報源の指定**: 参照すべき信頼できる情報源（公式サイト、IMDb、ウィキペディアなど）
3. **情報の補完方法**: 不足している情報をどのように補うべきか

## 出力形式

以下の形式で具体的な改善指示を提供してください：

```
フィールド名: <フィールド名>
現在のスコア: <スコア>
問題点: <簡潔な問題の説明>
改善提案:
- 検索クエリ: "<具体的な検索キーワード>"
- 参照すべき情報源: <情報源の例>
- 補完方法: <具体的な補完の指示>
```

すべてのフィールドが3.5以上の場合は「改善の必要なし」と記載してください。
"""


def build_improvement_proposal_prompt(
    movie_input: MovieInput,
    current_metadata: MovieMetadata,
    evaluation: MetadataEvaluationResult,
) -> str:
    """メタデータ改善提案用プロンプトを構築

    Args:
        movie_input: 映画の基本情報
        current_metadata: 現在のメタデータ
        evaluation: 評価結果

    Returns:
        構築されたプロンプト
    """

    def format_list(items: list[str]) -> str:
        """リストを読みやすい文字列に変換"""
        if not items or items == ["情報なし"]:
            return "情報なし"
        return "\n".join(f"  - {item}" for item in items)

    # 評価結果のサマリーを構築
    evaluation_lines = []
    for field_score in evaluation.field_scores:
        status = "✓ 合格" if field_score.score >= 3.5 else "✗ 要改善"
        evaluation_lines.append(
            f"- {field_score.field_name}: {field_score.score:.1f}/5.0 {status}\n"
            f"  理由: {field_score.reasoning}"
        )
    evaluation_summary = "\n".join(evaluation_lines)

    return IMPROVEMENT_PROPOSAL_PROMPT_TEMPLATE.format(
        title=movie_input.title,
        release_date=movie_input.release_date,
        country=movie_input.country,
        japanese_titles=format_list(current_metadata.japanese_titles),
        distributor=current_metadata.distributor,
        box_office=current_metadata.box_office,
        cast=format_list(current_metadata.cast),
        music=format_list(current_metadata.music),
        voice_actors=format_list(current_metadata.voice_actors),
        evaluation_summary=evaluation_summary,
    )
