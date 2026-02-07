# 映画メタ情報取得システム

Google GenAI SDKを使用して、CSVファイルから映画情報を読み込み、Google Search groundingで最新情報を補完し、構造化されたJSONを出力するシステムです。

## 機能

- CSVファイルから映画の基本情報（タイトル、公開日、制作国）を読み込み
- Google Search groundingで以下の情報を取得:
  - 配給会社
  - 興行収入
  - 主要な出演者
  - 楽曲/作曲家
  - 声優（アニメ/吹き替え）
- Pydanticスキーマで構造化されたJSONを出力

## 使用方法

### 全10件の映画を処理

```bash
cd /workspaces/learn-google-genai/app
uv run main.py
```

### テスト用（1件）

```bash
cd /workspaces/learn-google-genai/app
uv run python -c "from pathlib import Path; from movie_metadata.csv_reader import CSVReader; from movie_metadata.metadata_fetcher import fetch_movie_metadata; from movie_metadata.json_writer import JSONWriter; import os; reader = CSVReader(); movies = reader.read(Path('data/movies_test.csv')); api_key = os.getenv('GEMINI_API_KEY'); metadata_list = [fetch_movie_metadata(movies[0], api_key)]; JSONWriter().write(metadata_list, Path('data/output/test_output.json'))"
```

### テスト用（3件）

main.pyの22行目を以下のように変更:
```python
csv_path = Path(__file__).parent / "data" / "movies_test3.csv"
```

## モジュール構成

```
movie_metadata/
├── __init__.py          # パッケージ初期化
├── models.py            # Pydanticモデル定義
├── csv_reader.py        # CSV読み込みロジック
├── metadata_fetcher.py  # LLMメタデータ取得（コアロジック）
└── json_writer.py       # JSON出力ロジック
```

## 技術要件

- **モデル**: `gemini-3-flash-preview` (Gemini 3が必須)
- **Google Search Grounding**: 最新情報の補完
- **構造化出力**: Pydanticモデルでスキーマ定義

## データファイル

- `data/movies.csv` - 全10件のサンプル映画データ
- `data/movies_test.csv` - テスト用（1件）
- `data/movies_test3.csv` - テスト用（3件）
- `data/output/` - 出力JSONの保存先

## 出力例

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
  }
]
```

## エラーハンドリング

- API呼び出し失敗時はデフォルト値（"情報なし"）を返す
- レート制限対策として各リクエスト間に1秒待機
- CSV読み込みエラー時は警告を表示してスキップ

## 注意事項

- APIクォータの制限に注意（テスト時は少数で試す）
- Google Search groundingは検索クエリごとに課金される
- GEMINI_API_KEYが環境変数に設定されている必要がある
