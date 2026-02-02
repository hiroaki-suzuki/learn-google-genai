# 映画メタ情報取得システム - 実装計画

## 概要

Google GenAI SDKを使用して、CSVファイルから映画情報を読み込み、Google Search groundingで最新情報を補完し、Pydanticスキーマで構造化されたJSONを出力するシステムを実装します。

## 重要な技術要件

- **モデル**: `gemini-3-flash-preview` を使用（Gemini 3が必須）
  - Gemini 3でGoogle Search grounding + 構造化出力の組み合わせがサポートされている
- **Google Search Grounding**: CSVの映画の最新情報を補完
- **構造化出力**: Pydanticモデルを`response_schema`に渡してJSON形式で取得

## モジュール構成

```
app/
├── main.py                      # エントリーポイント（統合処理）
├── movie_metadata/              # 新規作成パッケージ
│   ├── __init__.py             # パッケージ初期化
│   ├── models.py               # Pydanticモデル定義
│   ├── csv_reader.py           # CSV読み込みロジック
│   ├── metadata_fetcher.py     # LLMメタデータ取得（コアロジック）
│   └── json_writer.py          # JSON出力ロジック
└── data/                        # 新規作成ディレクトリ
    ├── movies.csv              # 入力CSVファイル
    └── output/                 # 出力JSON格納先
```

## データモデル

### MovieInput (CSV読み込み用)
```python
class MovieInput(BaseModel):
    title: str
    release_date: str  # YYYY-MM-DD形式
    country: str
```

### MovieMetadata (LLM出力用)
```python
class MovieMetadata(BaseModel):
    title: str
    release_date: str
    country: str
    distributor: str              # 配給会社
    box_office: str               # 興行収入
    cast: List[str]               # 出演者
    music: List[str]              # 楽曲/作曲家
    voice_actors: List[str]       # 声優（アニメ/吹き替え）
```

各フィールドに`Field(description=...)`を追加し、情報が不明な場合は「情報なし」を返すよう指示。

## CSVサンプルデータ（10タイトル）

実在の映画（国際的な作品とアニメを含む）:
```csv
title,release_date,country
Spirited Away,2001-07-20,Japan
The Shawshank Redemption,1994-09-23,USA
Your Name,2016-08-26,Japan
Parasite,2019-05-30,South Korea
The Lion King,1994-06-24,USA
Inception,2010-07-16,USA
Frozen,2013-11-27,USA
The Dark Knight,2008-07-18,USA
My Neighbor Totoro,1988-04-16,Japan
Avengers: Endgame,2019-04-26,USA
```

## 実装詳細

### 1. models.py
- `MovieInput`と`MovieMetadata`のPydanticモデルを定義
- 各フィールドに詳細な`description`を追加（LLMへの指示として機能）

### 2. csv_reader.py
```python
def read_movies_csv(csv_path: str) -> List[MovieInput]:
    """CSVファイルから映画情報を読み込む"""
    # csv.DictReaderでCSVを読み込み
    # Pydanticでバリデーション
    # エラーハンドリング
```

### 3. json_writer.py
```python
def write_metadata_to_json(
    metadata_list: List[MovieMetadata],
    output_path: str,
) -> None:
    """メタデータをJSON形式で出力"""
    # json.dumpで整形出力
    # タイムスタンプ付きファイル名
```

### 4. metadata_fetcher.py（コアロジック）
```python
def fetch_movie_metadata(
    movie_input: MovieInput,
    api_key: str,
) -> MovieMetadata:
    """Google Search groundingで映画メタデータを取得"""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # プロンプト作成
    prompt = f"""
    以下の映画について、最新の情報をGoogle Searchで検索し、詳細なメタデータを提供してください:

    タイトル: {movie_input.title}
    公開日: {movie_input.release_date}
    制作国: {movie_input.country}

    以下の情報を取得してください:
    1. 配給会社（日本での配給会社を優先）
    2. 興行収入（世界興行収入または主要市場の興行収入）
    3. 主要な出演者（最大5名）
    4. 楽曲または作曲家（主題歌や劇伴）
    5. 声優（アニメの場合は日本語声優、実写の場合は日本語吹き替え声優）

    情報が見つからない項目については「情報なし」と記載してください。
    """

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
    metadata = MovieMetadata.model_validate_json(response.text)
    return metadata
```

### 5. main.py（統合処理）
```python
def main():
    # 環境変数からAPIキー取得
    api_key = os.getenv("GEMINI_API_KEY")

    # パス設定
    csv_path = Path(__file__).parent / "data" / "movies.csv"
    output_dir = Path(__file__).parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV読み込み
    movies = read_movies_csv(str(csv_path))

    # 各映画のメタデータを取得
    metadata_list = []
    for movie in movies:
        try:
            metadata = fetch_movie_metadata(movie, api_key)
            metadata_list.append(metadata)
            # レート制限対策: 1秒待機
            time.sleep(1)
        except Exception as e:
            print(f"エラー: {e}")
            continue

    # JSON出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"movie_metadata_{timestamp}.json"
    write_metadata_to_json(metadata_list, str(output_path))
```

## 実装順序

1. **models.py**: Pydanticモデル定義
2. **csv_reader.py**: CSV読み込み
3. **json_writer.py**: JSON出力
4. **metadata_fetcher.py**: LLMメタデータ取得（最も複雑）
5. **data/movies.csv**: サンプルCSVデータ作成
6. **main.py**: 全体統合
7. **テスト実行**: `cd app && uv run main.py`

## エラーハンドリング

- **CSV読み込み**: ファイル未存在、フォーマットエラーをキャッチ
- **API呼び出し**: タイムアウト、レート制限、パースエラーに対応
- **レート制限対策**: 各リクエスト間に1秒の遅延（`time.sleep(1)`）
- **情報未取得**: Pydanticのdescriptionで「情報なし」を返すよう指示

## 検証方法

### 段階的テスト
1. まず1件の映画でテスト（CSV上位1行のみ）
2. 成功したら3件でテスト
3. 最後に全10件でテスト

### 実行コマンド
```bash
cd /workspaces/learn-google-genai/app
uv run main.py
```

### 期待される出力
- コンソールに進捗表示: `[1/10] Spirited Away のメタデータを取得中...`
- `data/output/movie_metadata_YYYYMMDD_HHMMSS.json` に結果出力

### 出力JSONの例
```json
[
  {
    "title": "Spirited Away",
    "release_date": "2001-07-20",
    "country": "Japan",
    "distributor": "東宝",
    "box_office": "$395 million",
    "cast": ["柊瑠美", "入野自由", "夏木マリ", "内藤剛志", "沢口靖子"],
    "music": ["久石譲"],
    "voice_actors": ["柊瑠美", "入野自由", "夏木マリ"]
  },
  ...
]
```

## コード品質チェック

実装後、以下のコマンドで品質チェック:
```bash
cd /workspaces/learn-google-genai/app
uv run ruff format . && uv run ruff check --fix . && uv run ty check
```

## 重要な注意事項

1. **Gemini 3モデル必須**: `gemini-3-flash-preview`を使用しないと、Google Search grounding + 構造化出力の組み合わせが動作しない
2. **APIコスト**: Google Search groundingは検索クエリごとに課金されるため、テスト時は少数で試す
3. **レート制限**: 連続APIコールを避けるため、各リクエスト間に1秒待機
4. **プロンプトの重要性**: 「情報なし」を返すよう明示的に指示することで、エラー時のデフォルト値を保証

## Critical Files

実装で最も重要なファイル:

1. `/workspaces/learn-google-genai/app/movie_metadata/models.py` - データモデル定義（すべての基盤）
2. `/workspaces/learn-google-genai/app/movie_metadata/metadata_fetcher.py` - コアロジック（Google Search + 構造化出力）
3. `/workspaces/learn-google-genai/app/main.py` - エントリーポイント（全体統合）
4. `/workspaces/learn-google-genai/app/data/movies.csv` - 入力データ（10タイトル）

## 参考資料

- [Google GenAI Python SDK](https://googleapis.github.io/python-genai/)
- [Grounding with Google Search - Gemini API](https://ai.google.dev/gemini-api/docs/google-search)
- [Structured outputs - Gemini API](https://ai.google.dev/gemini-api/docs/structured-output)
