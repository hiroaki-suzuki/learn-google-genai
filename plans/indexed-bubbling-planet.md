# 映画メタ情報取得プログラムのリファクタリング設計

## Context (背景)

現在、`app/main.py`で映画メタ情報をGemini APIで取得するサンプルプログラムが動作していますが、サンプルレベルの構成のため、本番環境向けにリファクタリングが必要です。

### 現状の問題点

**緊急(実運用不可能)**:
1. **テストコード完全欠如** - ユニット/統合テストが存在しない
2. **ロギング機構なし** - `print()`のみで本番環境の運用に不適切
3. **設定がハードコード** - CSV/出力パス、モデル名、待機時間が固定
4. **APIエラーハンドリング不完全** - 汎用`Exception`キャッチで詳細なエラー対応ができない

**高(品質低下)**:
5. **型安全性が不完全** - `main.py`に型ヒントなし
6. **単一責任原則違反** - `metadata_fetcher.py`が複数責任、`main.py`が責任過剰
7. **監視機能なし** - 本番環境での可観測性が低い

### 現在のディレクトリ構成

```
app/
├── main.py (68行) - エントリーポイント
├── movie_metadata/
│   ├── models.py - Pydanticデータモデル(MovieInput, MovieMetadata)
│   ├── csv_reader.py - CSV入力処理(関数ベース)
│   ├── metadata_fetcher.py - Google GenAI API連携(関数ベース)
│   └── json_writer.py - JSON出力処理(関数ベース)
├── llm_judge/ - 既存の別ドメインパッケージ(参考)
└── data/
    ├── movies_test3.csv - 入力データ
    └── output/ - 出力ディレクトリ(※.gitignoreで除外されている)
```

### 技術スタック

- **Python**: 3.14
- **パッケージマネージャー**: uv
- **主要SDK**: google-genai (>=1.61.0)
- **バリデーション**: Pydantic
- **開発ツール**: Ruff (linter/formatter), Ty (型チェッカー)

---

## 設計検討: 3つの視点からの多角的分析

3つのエージェント視点(アーキテクチャ、批判的思考、テックリード)で検討した結果、以下の設計案が提案されました。

### 提案された設計案

**案1: シンプル案** - 最小限の変更(設定外部化、ロギング、テスト追加のみ)
- メリット: 実装コスト最小(2-3日)、既存構造維持
- デメリット: 拡張性が低い、依存性注入なし

**案2: 標準案** - Port & Adaptersパターン適用
- メリット: テスタビリティ高、拡張性高、責務明確
- デメリット: llm_judgeとの構造差異、学習コストあり

**案3: 堅牢案** - エンタープライズグレード(Circuit Breaker、メトリクス収集など)
- メリット: 本番運用で必要な全機能網羅
- デメリット: 過剰設計、複雑性高、実装コスト大(10-15日)

### 推奨案: 案1.5(シンプル案の改良版)

批判的思考から「案2はPort & Adaptersが現時点では過剰」「llm_judgeとの一貫性重視」という結論に至り、案1と案2のハイブリッド「案1.5」を推奨。

**主要な改善点**:
1. **設定の外部化** - `config.py`で環境変数とデフォルト値を管理
2. **ロギング機構** - 標準`logging`モジュールで構造化ログ
3. **APIクライアント分離** - `genai_client.py`で再利用可能なクライアント
4. **ビジネスロジック集約** - `metadata_service.py`で処理フロー管理
5. **コンポーネントのクラス化** - 依存性注入でテスタビリティ向上
6. **包括的なテスト** - pytest + pytest-mockでユニット/統合テスト

---

## 推奨ディレクトリ構成

```
app/
├── main.py (リファクタリング: 型ヒント追加、依存性注入)
├── config.py (NEW) - Pydantic Settings で設定管理
├── logging_config.py (NEW) - ロギング設定
├── movie_metadata/
│   ├── models.py (既存維持)
│   ├── csv_reader.py (クラス化: CSVReader)
│   ├── json_writer.py (クラス化: JSONWriter)
│   ├── genai_client.py (NEW) - GenAIClientクラス(APIクライアント分離)
│   ├── metadata_service.py (NEW) - MetadataServiceクラス(ビジネスロジック)
│   └── __init__.py
└── tests/ (NEW)
    ├── conftest.py - 共通フィクスチャ
    ├── test_csv_reader.py
    ├── test_json_writer.py
    ├── test_genai_client.py
    └── test_metadata_service.py
```

---

## 重要ファイルと責務

### 新規作成ファイル

#### 1. `app/config.py`
**責務**: 全設定の一元管理(環境変数、デフォルト値)

```python
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    csv_path: Path = Field(default=Path("data/movies_test3.csv"))
    output_dir: Path = Field(default=Path("data/output"))
    model_name: str = Field(default="gemini-3-flash-preview")
    rate_limit_sleep: float = Field(default=1.0)
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
```

#### 2. `app/logging_config.py`
**責務**: ロギング設定の初期化

```python
import logging
from pathlib import Path
from typing import Optional

def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=handlers
    )
```

#### 3. `app/movie_metadata/genai_client.py`
**責務**: Google GenAI APIクライアントのラッパー

- `metadata_fetcher.py`からAPIクライアント生成とAPI呼び出しロジックを分離
- 特定のAPIエラー(`RateLimitError`, `InvalidArgumentError`)を個別にキャッチ
- ロギング追加
- テスタビリティ向上(モック化が容易)

#### 4. `app/movie_metadata/metadata_service.py`
**責務**: ビジネスロジックの集約

- `main.py`から処理フローを移動
- CSV読込 → API取得 → JSON出力の一連の流れを管理
- 依存性注入で`CSVReader`, `JSONWriter`, `GenAIClient`を受け取る
- 処理結果を辞書で返却(`{"total": int, "success": int, "failed": int}`)

### 変更ファイル

#### 5. `app/main.py`
**変更内容**:
- 型ヒント追加(`def main() -> None`)
- 設定読み込み(`AppConfig()`)
- ロギング初期化(`setup_logging()`)
- 依存性注入パターン(各コンポーネントをインスタンス化して`MetadataService`に注入)
- ビジネスロジックを`MetadataService.process()`に委譲

#### 6. `app/movie_metadata/csv_reader.py`
**変更内容**:
- 関数ベースからクラスベース(`CSVReader`)に変更
- ロギング追加(`logger.info`, `logger.debug`)
- インターフェースは維持(`read(csv_path: Path) -> list[MovieInput]`)

#### 7. `app/movie_metadata/json_writer.py`
**変更内容**:
- 関数ベースからクラスベース(`JSONWriter`)に変更
- ロギング追加
- インターフェースは維持(`write(metadata_list: list[MovieMetadata], output_path: Path) -> None`)

#### 8. `app/pyproject.toml`
**追加依存関係**:
```toml
dependencies = [
    "google-genai>=1.61.0",
    "pydantic-settings>=2.0.0",  # NEW: 設定管理
]

[dependency-groups]
dev = [
    "ruff>=0.14.14",
    "ty>=0.0.14",
    "pytest>=8.0.0",         # NEW: テスト
    "pytest-mock>=3.12.0",   # NEW: モック
]
```

---

## 実装ロードマップ

### Phase 1: 緊急対応(優先度: 最高)
**目標**: 本番で最低限動作する状態

1. `config.py`作成 - 設定の外部化
2. `logging_config.py`作成 - ロギング機構
3. `main.py`に型ヒント追加
4. `metadata_fetcher.py`のエラーハンドリング改善(特定エラーの個別キャッチ)
5. 基本テスト追加(`test_csv_reader.py`, `test_json_writer.py`)

**成果物**: 設定外部化、ログ出力、基本的なエラーハンドリング

### Phase 2: 構造改善(優先度: 高)
**目標**: 保守性の高いコードベース

6. `genai_client.py`作成 - APIクライアント分離
7. `metadata_service.py`作成 - ビジネスロジック移動
8. `csv_reader.py`, `json_writer.py`のクラス化
9. `main.py`の依存性注入化
10. テスト拡充(`test_metadata_service.py`, `test_genai_client.py`)

**成果物**: テスタブルで拡張可能な構造

### Phase 3: 品質向上(優先度: 中)
**目標**: 本番運用可能な品質

11. 統合テストの追加(エンドツーエンド)
12. エラーケースのテスト拡充
13. ドキュメント整備(README更新、docstring充実)
14. CI/CD設定(GitHub Actionsでruff/ty/pytest自動実行)

**成果物**: 本番環境で安心して運用できる品質

---

## 検証方法

### 単体テスト
```bash
cd app
uv run pytest tests/ -v
```

### 統合テスト
```bash
cd app
uv run pytest tests/test_metadata_service.py -v
```

### コード品質チェック
```bash
cd app
uv run ruff format . && uv run ruff check --fix . && uv run ty check
```

### 実行確認
```bash
cd app
uv run main.py
```

期待される出力:
- ログがフォーマットされて出力(`%(asctime)s [%(levelname)s]...`)
- 環境変数から設定を読み込み
- 処理結果が明確に表示(`X/Y件成功`)
- エラー時に詳細なログ出力

---

## 設計上の重要な判断

### 1. クラス化 vs 関数ベース
**判断**: コンポーネントをクラス化(CSVReader, JSONWriter, GenAIClient, MetadataService)

**理由**:
- 依存性注入によるテスタビリティ向上
- 状態管理が明確(APIクライアントの再利用など)
- モック化が容易

**懸念点**: llm_judgeは関数ベースのまま → 一貫性の問題

### 2. Port & Adaptersパターンの見送り
**判断**: 抽象インターフェース(Protocol)を作らず、具象クラスを直接使用

**理由**:
- 現時点で複数の入力形式(CSV以外)の予定がない
- 過剰設計を避ける(YAGNI原則)
- シンプルさを維持

**将来の拡張時**: 必要に応じてProtocolを導入可能

### 3. llm_judgeとの一貫性
**現状**: llm_judgeも同様の問題(関数ベース、APIクライアント内部生成、エラーハンドリング不完全)を抱えている

**判断保留**: llm_judgeも同時にリファクタリングするか、movie_metadataのみ先行するか要確認

---

## リスクと対策

### リスク1: クラス化による複雑性増加
**対策**: 最小限のクラス構成(4クラスのみ)、インターフェースはシンプルに保つ

### リスク2: llm_judgeとの構造差異
**対策**: 共通の`genai_client.py`を作成し、両方のモジュールで再利用可能にする

### リスク3: 実装コスト
**対策**: Phase 1のみ先行実装し、効果を確認してからPhase 2/3に進む

---

## 確定した実装方針

ユーザーとの協議により、以下の方針が確定しました:

1. **対象範囲**: movie_metadataのみ先行実装
   - llm_judgeは学習用サンプルとして現状維持
   - 将来的にllm_judgeもリファクタリングする場合は、movie_metadataの経験を活かす

2. **実装スタイル**: クラスベース(提案通り)
   - 依存性注入でテスタビリティを確保
   - llm_judgeとの構造差異は許容(目的が異なるため)

3. **実装範囲**: Phase 1のみ(緊急対応)
   - 設定外部化、ロギング、基本テストに集中
   - 効果を確認してからPhase 2/3を検討

---

## Phase 1 実装詳細

### 実装タスク一覧

#### タスク1: 設定管理の外部化
**ファイル**: `app/config.py` (新規作成)

**内容**:
```python
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """アプリケーション設定"""

    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    csv_path: Path = Field(default=Path("data/movies_test3.csv"))
    output_dir: Path = Field(default=Path("data/output"))
    model_name: str = Field(default="gemini-3-flash-preview")
    rate_limit_sleep: float = Field(default=1.0)
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
```

**理由**: ハードコードされた設定を環境変数化し、異なる環境(dev/staging/prod)で柔軟に対応できるようにする。

---

#### タスク2: ロギング機構の導入
**ファイル**: `app/logging_config.py` (新規作成)

**内容**:
```python
import logging
from pathlib import Path
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """ロギング設定を初期化

    Args:
        level: ログレベル (DEBUG/INFO/WARNING/ERROR)
        log_file: ログファイルパス (オプション)
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
```

**変更**: 全モジュール(csv_reader, json_writer, metadata_fetcher)で`print()`を`logger.info()`, `logger.warning()`, `logger.error()`に置き換え

**理由**: 本番環境での運用性向上。ログレベルによる出力制御、ファイル出力対応。

---

#### タスク3: main.pyに型ヒント追加
**ファイル**: `app/main.py` (変更)

**変更前**:
```python
def main():
    print("=== 映画メタ情報取得システム ===\n")
    # ...
```

**変更後**:
```python
import logging
from config import AppConfig
from logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """映画メタ情報取得システムのメインエントリーポイント"""
    # 設定読み込み
    config = AppConfig()

    # ロギング設定
    setup_logging(config.log_level)
    logger.info("=== 映画メタ情報取得システム起動 ===")

    # 環境変数チェック(config.pyで自動検証されるので削除可能)
    # ...
```

**理由**: 型安全性の向上、Ty型チェッカーでの検証可能化。

---

#### タスク4: metadata_fetcher.pyのエラーハンドリング改善
**ファイル**: `app/movie_metadata/metadata_fetcher.py` (変更)

**変更箇所**: 78-91行目の汎用Exception catchを特定エラーの個別キャッチに変更

**変更前**:
```python
except Exception as e:
    print(f"  警告: メタデータ取得に失敗しました ({type(e).__name__}: {e})")
    return MovieMetadata(...)
```

**変更後**:
```python
import logging
from google import genai

logger = logging.getLogger(__name__)

try:
    # API呼び出し
    response = client.models.generate_content(...)
    # ...
except genai.errors.RateLimitError as e:
    logger.error(f"Rate limit exceeded for {movie_input.title}: {e}")
    raise
except genai.errors.InvalidArgumentError as e:
    logger.error(f"Invalid argument for {movie_input.title}: {e}")
    raise
except ValueError as e:
    logger.warning(f"Empty response for {movie_input.title}: {e}")
    # デフォルト値を返す
    return MovieMetadata(
        title=movie_input.title,
        japanese_titles=["情報なし"],
        # ...
    )
except Exception as e:
    logger.exception(f"Unexpected error for {movie_input.title}")
    raise
```

**理由**: エラーの種類を識別し、適切な対処(リトライ、スキップ、エラー報告)を行う。

---

#### タスク5: 基本テストの追加
**ファイル**:
- `app/tests/conftest.py` (新規作成) - 共通フィクスチャ
- `app/tests/test_csv_reader.py` (新規作成)
- `app/tests/test_json_writer.py` (新規作成)

**test_csv_reader.py**:
```python
import pytest
from pathlib import Path
from movie_metadata.csv_reader import read_movies_csv
from movie_metadata.models import MovieInput


def test_read_movies_csv_success(tmp_path: Path):
    """正常なCSV読み込みテスト"""
    # Arrange
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "title,release_date,country\n"
        "Test Movie,2024-01-01,Japan\n"
    )

    # Act
    movies = read_movies_csv(str(csv_file))

    # Assert
    assert len(movies) == 1
    assert movies[0].title == "Test Movie"
    assert movies[0].release_date == "2024-01-01"
    assert movies[0].country == "Japan"


def test_read_movies_csv_file_not_found():
    """ファイル不在時のエラーテスト"""
    with pytest.raises(FileNotFoundError):
        read_movies_csv("nonexistent.csv")


def test_read_movies_csv_invalid_header(tmp_path: Path):
    """ヘッダー不正時のエラーテスト"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("invalid,header\n")

    with pytest.raises(ValueError, match="必須フィールド"):
        read_movies_csv(str(csv_file))
```

**test_json_writer.py**:
```python
import json
import pytest
from pathlib import Path
from movie_metadata.json_writer import write_metadata_to_json
from movie_metadata.models import MovieMetadata


def test_write_metadata_to_json(tmp_path: Path):
    """正常なJSON書き込みテスト"""
    # Arrange
    metadata_list = [
        MovieMetadata(
            title="Test Movie",
            japanese_titles=["テスト映画"],
            release_date="2024-01-01",
            country="Japan",
            distributor="テスト配給",
            box_office="$1M",
            cast=["俳優A"],
            music=["作曲家B"],
            voice_actors=["声優C"],
        )
    ]
    output_file = tmp_path / "output.json"

    # Act
    write_metadata_to_json(metadata_list, str(output_file))

    # Assert
    assert output_file.exists()
    with output_file.open(encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["title"] == "Test Movie"
```

**conftest.py**:
```python
import pytest
from pathlib import Path


@pytest.fixture
def sample_movie_input():
    """テスト用MovieInputフィクスチャ"""
    from movie_metadata.models import MovieInput

    return MovieInput(
        title="Test Movie",
        release_date="2024-01-01",
        country="Japan"
    )
```

**理由**: 基本的な入出力処理の動作保証。リグレッションテストの基盤。

---

#### タスク6: pyproject.tomlの更新
**ファイル**: `app/pyproject.toml` (変更)

**追加内容**:
```toml
dependencies = [
    "google-genai>=1.61.0",
    "pydantic-settings>=2.0.0",
]

[dependency-groups]
dev = [
    "ruff>=0.14.14",
    "ty>=0.0.14",
    "pytest>=8.0.0",
    "pytest-mock>=3.12.0",
]
```

**実行**: `cd app && uv sync`

**理由**: 新しい依存関係(pydantic-settings, pytest)のインストール。

---

### Phase 1 完了後の状態

```
app/
├── main.py (型ヒント追加、設定/ロギング統合)
├── config.py (NEW) ✓
├── logging_config.py (NEW) ✓
├── movie_metadata/
│   ├── models.py (既存)
│   ├── csv_reader.py (ロギング追加)
│   ├── metadata_fetcher.py (エラーハンドリング改善、ロギング追加)
│   └── json_writer.py (ロギング追加)
└── tests/ (NEW) ✓
    ├── conftest.py ✓
    ├── test_csv_reader.py ✓
    └── test_json_writer.py ✓
```

### Phase 1 検証方法

1. **依存関係インストール**:
   ```bash
   cd app
   uv sync
   ```

2. **テスト実行**:
   ```bash
   cd app
   uv run pytest tests/ -v
   ```
   期待結果: 全テストがPASS

3. **型チェック**:
   ```bash
   cd app
   uv run ty check
   ```
   期待結果: エラーなし

4. **リント/フォーマット**:
   ```bash
   cd app
   uv run ruff format .
   uv run ruff check --fix .
   ```

5. **実行確認**:
   ```bash
   cd app
   uv run main.py
   ```
   期待される出力:
   ```
   2026-02-06 10:00:00 [INFO] __main__: === 映画メタ情報取得システム起動 ===
   2026-02-06 10:00:01 [INFO] movie_metadata.csv_reader: Successfully read 3 movies from data/movies_test3.csv
   2026-02-06 10:00:01 [INFO] movie_metadata.metadata_fetcher: Fetching metadata for: Spirited Away
   ...
   ```

---

### Phase 2以降への移行判断

Phase 1完了後、以下を評価:
1. ロギングの有効性(デバッグが容易になったか?)
2. テストの網羅性(バグ検出できるか?)
3. 設定外部化の効果(環境切り替えが容易か?)

効果が確認できた場合、Phase 2(構造改善)に進む:
- genai_client.py分離
- metadata_service.py作成
- クラス化(CSVReader, JSONWriter)
- 依存性注入

---

## 重要な注意事項

### llm_judgeとの関係
- llm_judgeは現状維持(関数ベース)
- movie_metadataのみクラスベース化
- 両者の構造差異は許容(目的が異なるため問題ない)
- 将来的にllm_judgeもリファクタリングする場合は、movie_metadataの設計を参考にする

### クラス化は将来対応
- Phase 1ではクラス化しない(関数ベース維持)
- ロギング、設定外部化、エラーハンドリング改善に集中
- Phase 2でクラス化を実施

### 段階的アプローチの利点
- リスクを最小化
- 各フェーズで効果を確認
- 必要に応じて方針変更可能
