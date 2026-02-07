---
name: code-style
description: Pythonのコーディングスタイルを守るためのスキル
---

# コードスタイル

- Ruff (`ruff.toml`) の設定に従う
- フォーマット: `uv run ruff format`
- リント: `uv run ruff check`（`--fix` で自動修正可）
- 型チェック: `uv run ty check`

## 命名規則（PEP 8）
- 変数・関数・メソッド: snake_case
- クラス: PascalCase
- 定数: UPPER_SNAKE_CASE
- プライベート: `_` プレフィックス

## 型ヒント
- 関数の引数と戻り値には型ヒントを付ける
- `Any` は避け、具体的な型を使用
- コレクションは `list[str]`, `dict[str, int]` のようにジェネリクス表記
