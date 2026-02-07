# GenAIClientコンテキストマネージャー対応

## Context（背景）

現在の`GenAIClient`は内部で`genai.Client`を保持していますが、明示的なリソースクリーンアップ機構がありません。`genai.Client`はHTTPコネクションなどのリソースを管理しており、公式ドキュメントではコンテキストマネージャーでの使用が推奨されています。

現在の問題点：
- `main.py`でインスタンス化後、プログラム終了までリソースが保持される
- 明示的な`close()`メソッドがない
- 長時間実行時のリソースリークのリスク

この変更により、`GenAIClient`をコンテキストマネージャーとして使用できるようにし、適切なリソース管理を可能にします。

## 実装内容

### 1. GenAIClientの修正

**ファイル**: `app/movie_metadata/genai_client.py`

以下のメソッドを追加：

```python
def __enter__(self) -> "GenAIClient":
    """コンテキストマネージャーのエントリーポイント"""
    logger.debug("GenAIClient context manager entered")
    return self

def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback: object | None,
) -> None:
    """コンテキストマネージャーの終了処理"""
    logger.debug(
        f"GenAIClient context manager exiting "
        f"(exception={'yes' if exc_type else 'no'})"
    )
    self.close()

def close(self) -> None:
    """クライアントをクローズし、リソースを解放"""
    try:
        logger.info("Closing GenAIClient and releasing resources")
        self._client.close()
    except Exception as e:
        logger.warning(f"Error during GenAIClient.close(): {e}")
```

**クラスdocstringの更新**:
- コンテキストマネージャーとしての使用例を追加
- 明示的`close()`の使用例を追加

### 2. テストの追加

**ファイル**: `app/tests/test_genai_client.py`

`TestGenAIClientContextManager`クラスを追加し、以下をテスト：
- `__enter__`が`self`を返すこと
- `__exit__`が`close()`を呼び出すこと
- `with`文で正常に使用できること
- 例外発生時でも`close()`が呼ばれること
- `close()`が内部clientの`close()`を委譲すること
- `close()`のエラーが抑制されること
- 複数回`close()`を呼んでも安全であること

### 3. main.pyの更新（推奨）

**ファイル**: `app/main.py`

コンテキストマネージャーパターンに変更：

```python
def main() -> None:
    """映画メタ情報取得システムのメインエントリーポイント"""
    config = AppConfig()
    setup_logging(config.log_level)
    logger.info("=== 映画メタ情報取得システム起動 ===")

    with GenAIClient(
        api_key=config.gemini_api_key,
        model_name=config.model_name,
    ) as client:
        csv_reader = CSVReader()
        json_writer = JSONWriter()

        service = MetadataService(
            client=client,
            csv_reader=csv_reader,
            json_writer=json_writer,
            rate_limit_sleep=config.rate_limit_sleep,
        )

        csv_path = Path(__file__).parent / config.csv_path
        output_dir = Path(__file__).parent / config.output_dir

        try:
            result = service.process(csv_path, output_dir)
            logger.info(
                f"処理結果: {result['success']}/{result['total']}件成功, "
                f"{result['failed']}件失敗"
            )
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")
```

## Critical Files

実装に重要な3つのファイル：

1. **`app/movie_metadata/genai_client.py`** - `__enter__`/`__exit__`/`close()`メソッドを実装
2. **`app/tests/test_genai_client.py`** - 新機能のユニットテストを追加
3. **`app/main.py`** - コンテキストマネージャーパターンで使用（推奨）

## 設計判断

- **後方互換性**: 既存のインスタンス化パターン（`client = GenAIClient(...)`）も引き続き動作
- **エラーハンドリング**: `close()`内のエラーはログに記録するが、呼び出し元には伝播しない
- **複数close()**: 複数回呼び出しても安全（内部clientに委譲）
- **非同期サポート**: 現時点では実装しない（現在のコードベースは同期APIのみ使用）

## 検証方法

### 1. ユニットテスト実行

```bash
cd app
uv run pytest tests/test_genai_client.py::TestGenAIClientContextManager -v
```

### 2. 既存テストの回帰確認

```bash
cd app
uv run pytest tests/ -v
```

### 3. コード品質チェック

```bash
cd app
uv run ruff format . && uv run ruff check --fix . && uv run ty check
```

### 4. 手動動作確認

```bash
cd app
LOG_LEVEL=DEBUG uv run main.py
```

ログ出力で以下を確認：
- `"GenAIClient context manager entered"`
- `"GenAIClient context manager exiting"`
- `"Closing GenAIClient and releasing resources"`

## 期待される結果

- `GenAIClient`が`with`文で使用可能になる
- リソースが自動的にクリーンアップされる
- 既存のコードは引き続き動作する（後方互換性）
- 全てのテストが成功する
