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

### 2. original_work (原作)
{original_work}

### 3. original_authors (原作者)
{original_authors}

### 4. distributor (配給会社)
{distributor}

### 5. production_companies (制作会社)
{production_companies}

### 6. box_office (興行収入)
{box_office}

### 7. cast (主要な出演者)
{cast}

### 8. screenwriters (脚本家)
{screenwriters}

### 9. music (楽曲または作曲家)
{music}

### 10. voice_actors (声優)
{voice_actors}

## 評価基準

以下の10個のフィールドについて、それぞれ0.0〜5.0のスコアで評価してください。

### 評価観点

各フィールドは以下の3つの観点で評価してください：

1. **完全性 (Completeness)**: 情報が十分に含まれているか
   - 5.0点: 完全で詳細な情報が含まれている
   - 4.0点以上: 十分な情報があり、基本的に満足できる
   - 2.0点: 情報が大幅に不足している
   - 0.0点: 情報が全くない、または「情報なし」と記載されている

2. **正確性 (Accuracy)**: 情報が正確で信頼できるか
   - 5.0点: 明らかに正確で、詳細度が高い
   - 4.0点以上: 概ね正確で、信頼できる
   - 2.0点: 不正確または疑わしい情報を含む
   - 0.0点: 明らかに誤っている

3. **有用性 (Usefulness)**: 情報が有用で価値があるか
   - 5.0点: 非常に有用で、詳細な情報を提供している
   - 4.0点以上: 基本的に有用で、実用的な価値がある
   - 2.0点: 限定的な有用性
   - 0.0点: 全く有用でない

### フィールド別の評価ポイント

- **japanese_titles**: 正式名称、略称、別名など複数の呼び方が含まれているか
- **original_work**: 原作がある場合は作品名が明記されているか、
  オリジナルなら「オリジナル」と記載されているか
- **original_authors**: 原作者が正確に記載されているか（オリジナルの場合は空でも可）
- **distributor**: 日本での配給会社が明記されているか
- **production_companies**: 主要な制作会社が適切にリストされているか
- **box_office**: 通貨単位を含む具体的な金額が記載されているか
- **cast**: 主要な出演者が適切な人数（最大5名程度）リストされているか
- **screenwriters**: 脚本家が適切にリストされているか
- **music**: 主題歌や劇伴作曲家など、具体的な楽曲情報が含まれているか
- **voice_actors**: アニメの場合は日本語声優、実写の場合は
  吹き替え声優が適切にリストされているか

## 閾値

**合格基準**: すべてのフィールドが設定された閾値以上

## 出力形式

各フィールドのスコアと理由、および改善提案を提供してください。
- スコアが閾値未満のフィールドについては、具体的な改善提案を含めてください
- すべてのフィールドが閾値以上の場合、improvement_suggestionsは「なし」としてください
"""


def build_metadata_evaluation_prompt(
    title: str,
    release_date: str,
    country: str,
    japanese_titles: list[str],
    original_work: str,
    original_authors: list[str],
    distributor: str,
    production_companies: list[str],
    box_office: str,
    cast: list[str],
    screenwriters: list[str],
    music: list[str],
    voice_actors: list[str],
) -> str:
    """メタデータ評価用プロンプトを構築

    Args:
        title: 映画タイトル
        release_date: 公開日
        country: 制作国
        japanese_titles: 日本語タイトルのリスト
        original_work: 原作
        original_authors: 原作者のリスト
        distributor: 配給会社
        production_companies: 制作会社のリスト
        box_office: 興行収入
        cast: 主要な出演者のリスト
        screenwriters: 脚本家のリスト
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

    def format_value(value: str) -> str:
        """文字列を読みやすい形式に変換"""
        if not value or value == "情報なし":
            return "情報なし"
        return value

    return METADATA_EVALUATION_PROMPT_TEMPLATE.format(
        title=title,
        release_date=release_date,
        country=country,
        japanese_titles=format_list(japanese_titles),
        original_work=format_value(original_work),
        original_authors=format_list(original_authors),
        distributor=distributor,
        production_companies=format_list(production_companies),
        box_office=box_office,
        cast=format_list(cast),
        screenwriters=format_list(screenwriters),
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

### 2. original_work (原作)
{original_work}

### 3. original_authors (原作者)
{original_authors}

### 4. distributor (配給会社)
{distributor}

### 5. production_companies (制作会社)
{production_companies}

### 6. box_office (興行収入)
{box_office}

### 7. cast (主要な出演者)
{cast}

### 8. screenwriters (脚本家)
{screenwriters}

### 9. music (楽曲または作曲家)
{music}

### 10. voice_actors (声優)
{voice_actors}

## 評価結果

{evaluation_summary}

## タスク

スコアが閾値未満のフィールドについて、以下の形式で改善提案を生成してください：

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

すべてのフィールドが閾値以上の場合は「改善の必要なし」と記載してください。
"""


def build_improvement_proposal_prompt(
    movie_input: MovieInput,
    current_metadata: MovieMetadata,
    evaluation: MetadataEvaluationResult,
    threshold: float,
) -> str:
    """メタデータ改善提案用プロンプトを構築

    Args:
        movie_input: 映画の基本情報
        current_metadata: 現在のメタデータ
        evaluation: 評価結果
        threshold: 品質スコアの閾値

    Returns:
        構築されたプロンプト
    """

    def format_list(items: list[str]) -> str:
        """リストを読みやすい文字列に変換"""
        if not items or items == ["情報なし"]:
            return "情報なし"
        return "\n".join(f"  - {item}" for item in items)

    def format_value(value: str) -> str:
        """文字列を読みやすい形式に変換"""
        if not value or value == "情報なし":
            return "情報なし"
        return value

    # 評価結果のサマリーを構築
    evaluation_lines = []
    for field_score in evaluation.field_scores:
        status = "✓ 合格" if field_score.score >= threshold else "✗ 要改善"
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
        original_work=format_value(current_metadata.original_work),
        original_authors=format_list(current_metadata.original_authors),
        distributor=current_metadata.distributor,
        production_companies=format_list(current_metadata.production_companies),
        box_office=current_metadata.box_office,
        cast=format_list(current_metadata.cast),
        screenwriters=format_list(current_metadata.screenwriters),
        music=format_list(current_metadata.music),
        voice_actors=format_list(current_metadata.voice_actors),
        evaluation_summary=evaluation_summary,
    )


# ========================================
# メタデータ再取得（改善版）用プロンプト
# ========================================


def build_metadata_fetch_prompt(
    input_info: str, improvement_instruction: str | None = None
) -> str:
    """メタデータ取得用プロンプトを構築

    Args:
        input_info: 映画の基本情報
        improvement_instruction: 改善指示（任意）

    Returns:
        構築されたプロンプト
    """
    base_prompt = f"""
# 映画メタデータ取得タスク

以下の映画について、最新の情報をGoogle Searchで検索し、
詳細なメタデータを提供してください。

## 映画情報
{input_info}

## 情報収集の指針
- すべてのメタ情報は**日本語の情報を優先的に使用**してください
- 日本語の情報が見つからない場合のみ、
  英語など他の言語の情報を使用してください
- 人名や固有名詞は、可能な限り日本語表記（カタカナまたは漢字）
  で提供してください

## 出力するメタ情報
- japanese_titles
- original_work
- original_authors
- distributor
- production_companies
- box_office
- cast
- screenwriters
- music
- voice_actors

## エラーハンドリング
- 情報が見つからない項目については「情報なし」と記載してください
- リスト形式の項目で情報がない場合は、空のリストを返してください
"""

    if improvement_instruction:
        improvement_section = f"""
## 改善指示

前回の取得結果を改善するために、以下の点に注意してください：

{improvement_instruction}

上記の指示に従って、より正確で詳細な情報を取得してください。
"""
        return base_prompt + improvement_section

    return base_prompt
