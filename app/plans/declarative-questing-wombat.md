# 閾値のハードコード問題修正計画

## Context（背景）

前回のセッションで、ログや環境変数の閾値不一致を修正しましたが、いくつかのハードコードされた閾値が残っています。ユーザーは「QUALITY_SCORE_THRESHOLDが取れる前提で修正を検討してください」と要求しており、環境変数から値を取得し、ハードコードを削除する必要があります。

### 現在の環境変数設定
- `config.py`: `quality_score_threshold`のデフォルト値は**4.0**
- 環境変数: `QUALITY_SCORE_THRESHOLD` (未設定時は4.0を使用)

### 特定した問題

1. **evaluator.py**: デフォルト値が`4.5`とハードコード（config.pyのデフォルト4.0と不一致）
2. **prompts.py**: `build_improvement_proposal_prompt`関数内で閾値`4.5`がハードコード
   - TODO コメントあり: "閾値をパラメータ化する"

## 実装計画

### 1. evaluator.py の修正

**ファイル**: `/workspaces/learn-google-genai/app/movie_metadata/evaluator.py`

**変更内容**:
- `__init__`メソッドのthresholdパラメータのデフォルト値を`4.5`から`4.0`に変更
- これによりconfig.pyのデフォルト値と一致させる

```python
# 現在 (36行目):
def __init__(
    self, api_key: str, model_name: str = "gemini-2.0-flash", threshold: float = 4.5
) -> None:

# 修正後:
def __init__(
    self, api_key: str, model_name: str = "gemini-2.0-flash", threshold: float = 4.0
) -> None:
```

**理由**: refiner.pyが常にconfig.quality_score_thresholdを渡すため、デフォルト値はconfig.pyと一致させるべき

### 2. prompts.py の修正

**ファイル**: `/workspaces/learn-google-genai/app/movie_metadata/prompts.py`

**変更内容**:
- `build_improvement_proposal_prompt`関数にthresholdパラメータを追加
- ハードコードされた`threshold = 4.5`を削除
- TODOコメントを削除

```python
# 現在 (251-306行目):
def build_improvement_proposal_prompt(
    movie_input: MovieInput,
    current_metadata: MovieMetadata,
    evaluation: MetadataEvaluationResult,
) -> str:
    # ...
    # 評価結果のサマリーを構築（閾値は4.5と仮定、実際の値は環境変数による）
    # TODO: 閾値をパラメータ化する
    threshold = 4.5

# 修正後:
def build_improvement_proposal_prompt(
    movie_input: MovieInput,
    current_metadata: MovieMetadata,
    evaluation: MetadataEvaluationResult,
    threshold: float,
) -> str:
    # ...
    # 評価結果のサマリーを構築
    evaluation_lines = []
```

### 3. improvement_proposer.py の修正

**ファイル**: `/workspaces/learn-google-genai/app/movie_metadata/improvement_proposer.py`

**変更内容**:
- `__init__`メソッドにthresholdパラメータを追加
- `propose`メソッドで`build_improvement_proposal_prompt`に閾値を渡す

```python
# 現在 (34-37行目):
def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash") -> None:
    self.api_key = api_key
    self.model_name = model_name

# 修正後:
def __init__(
    self, api_key: str, model_name: str = "gemini-2.0-flash", threshold: float = 4.0
) -> None:
    self.api_key = api_key
    self.model_name = model_name
    self.threshold = threshold
```

```python
# 現在 (70-74行目):
prompt = build_improvement_proposal_prompt(
    movie_input=movie_input,
    current_metadata=current_metadata,
    evaluation=evaluation,
)

# 修正後:
prompt = build_improvement_proposal_prompt(
    movie_input=movie_input,
    current_metadata=current_metadata,
    evaluation=evaluation,
    threshold=self.threshold,
)
```

### 4. refiner.py の修正

**ファイル**: `/workspaces/learn-google-genai/app/movie_metadata/refiner.py`

**変更内容**:
- ImprovementProposer初期化時に閾値を渡す

```python
# 現在 (58行目):
self.proposer = ImprovementProposer(api_key=api_key, model_name=model_name)

# 修正後:
self.proposer = ImprovementProposer(
    api_key=api_key, model_name=model_name, threshold=self.default_threshold
)
```

```python
# refineメソッド内で閾値が更新された場合、proposerの閾値も更新
# 108行目の後に追加:
self.evaluator.threshold = threshold
self.proposer.threshold = threshold  # 追加
```

### 5. テストファイルの修正

**影響を受けるテストファイル**:
- `/workspaces/learn-google-genai/app/tests/test_improvement_proposer.py`
- `/workspaces/learn-google-genai/app/tests/test_prompts.py`

**test_improvement_proposer.py の変更**:
- ImprovementProposerの初期化時にthresholdパラメータを追加

```python
# 例: test_proposer_initialization (69-73行目)
def test_proposer_initialization():
    """ImprovementProposerの初期化テスト"""
    proposer = ImprovementProposer(
        api_key="test_key", model_name="gemini-2.0-flash", threshold=3.5
    )
    assert proposer.api_key == "test_key"
    assert proposer.model_name == "gemini-2.0-flash"
    assert proposer.threshold == 3.5  # 追加
```

**test_prompts.py の変更**:
- `build_improvement_proposal_prompt`の呼び出しにthresholdパラメータを追加

```python
# 例: test_build_prompt_with_fail_status (186-190行目)
prompt = build_improvement_proposal_prompt(
    movie_input=movie_input,
    current_metadata=current_metadata,
    evaluation=evaluation,
    threshold=4.5,  # 追加
)
```

## クリティカルファイル

1. `/workspaces/learn-google-genai/app/config.py` - 環境変数定義
2. `/workspaces/learn-google-genai/app/movie_metadata/evaluator.py` - 閾値デフォルト値
3. `/workspaces/learn-google-genai/app/movie_metadata/prompts.py` - ハードコード閾値
4. `/workspaces/learn-google-genai/app/movie_metadata/improvement_proposer.py` - 閾値受け渡し
5. `/workspaces/learn-google-genai/app/movie_metadata/refiner.py` - 閾値管理
6. `/workspaces/learn-google-genai/app/tests/test_improvement_proposer.py` - テスト更新
7. `/workspaces/learn-google-genai/app/tests/test_prompts.py` - テスト更新

## 検証計画

### 1. ユニットテスト実行
```bash
cd app
uv run pytest -v
```
すべてのテストがpassすることを確認

### 2. コード品質チェック
```bash
cd app
uv run ruff format . && uv run ruff check --fix . && uv run ty check
```

### 3. 動作確認
- 環境変数が未設定の場合、デフォルト値4.0が使用されることを確認
- 環境変数を設定した場合、その値が使用されることを確認
- ログ出力に正しい閾値が表示されることを確認

## 予想される影響範囲

- **低リスク**: ほとんどの変更はパラメータ追加で、既存の動作は維持される
- **テスト更新が必要**: `test_improvement_proposer.py`と`test_prompts.py`
- **後方互換性**: デフォルト値を提供するため、既存コードへの影響は最小限

## まとめ

この修正により:
1. すべての閾値がconfig.pyの`quality_score_threshold`（デフォルト4.0）から取得される
2. ハードコードされた閾値がすべて削除される
3. 環境変数`QUALITY_SCORE_THRESHOLD`で閾値を一元管理できる
4. コードの一貫性と保守性が向上する
