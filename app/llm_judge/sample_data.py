"""LLM as a Judge用のサンプルデータ"""

from llm_judge.models import Answer, Question

# ========================================
# サンプル質問
# ========================================

SAMPLE_QUESTIONS = [
    Question(
        question_id="q001",
        text="Pythonのリスト内包表記とは何ですか？利点と使用例を教えてください。",
        category="プログラミング",
    ),
    Question(
        question_id="q002",
        text="機械学習における過学習とは何ですか？どのように防ぐことができますか?",
        category="機械学習",
    ),
    Question(
        question_id="q003",
        text="PythonとJavaScriptの主な違いは何ですか？",
        category="比較分析",
    ),
]

# ========================================
# サンプル回答 (品質レベル別)
# ========================================

# 質問1: Pythonのリスト内包表記
Q1_EXCELLENT_ANSWER = Answer(
    answer_id="q001_excellent",
    text="""
Pythonのリスト内包表記は、既存のイテラブルから新しいリストを作成するための簡潔な構文です。

**基本構文**:
```python
[式 for 要素 in イテラブル if 条件]
```

**主な利点**:
1. **可読性**: 意図が明確で読みやすい
2. **簡潔性**: forループより短く書ける
3. **パフォーマンス**: 通常のforループより高速

**使用例**:
```python
# 基本的な変換
squares = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# 条件付きフィルタリング
even_squares = [x**2 for x in range(10) if x % 2 == 0]
# [0, 4, 16, 36, 64]

# 文字列処理
words = ["hello", "world", "python"]
upper_words = [w.upper() for w in words]
# ['HELLO', 'WORLD', 'PYTHON']
```

**使用上の注意**:
- 複雑な処理には通常のforループの方が読みやすい
- 大規模データではジェネレータ式 `()` の使用を検討
""",
)

Q1_GOOD_ANSWER = Answer(
    answer_id="q001_good",
    text="""
リスト内包表記は、Pythonでリストを効率的に作成する方法です。

**構文**:
```python
[式 for 要素 in イテラブル]
```

**利点**:
- コードが短くなる
- 読みやすい
- 実行速度が速い

**例**:
```python
# 1から10の2乗のリスト
squares = [x**2 for x in range(1, 11)]

# 偶数のみフィルタリング
even_numbers = [x for x in range(20) if x % 2 == 0]
```

forループより簡潔で、Pythonらしいコードが書けます。
""",
)

Q1_MEDIUM_ANSWER = Answer(
    answer_id="q001_medium",
    text="""
リスト内包表記は、リストを簡単に作る方法です。

例:
```python
numbers = [x for x in range(10)]
```

これは、forループで書くより短くなります。便利な機能です。
""",
)

Q1_POOR_ANSWER = Answer(
    answer_id="q001_poor",
    text="""
リスト内包表記は、Pythonの機能です。リストを作るときに使います。
""",
)

# 質問2: 機械学習における過学習
Q2_EXCELLENT_ANSWER = Answer(
    answer_id="q002_excellent",
    text="""
過学習(Overfitting)は、機械学習モデルが訓練データに過度に適合し、未知のデータに対する汎化性能が低下する現象です。

**過学習の症状**:
- 訓練データでの精度は高いが、テストデータでの精度が低い
- モデルが訓練データのノイズまで学習してしまう
- 複雑すぎるモデルで発生しやすい

**防止策**:

1. **データ拡張**
   - 訓練データを増やす
   - データ拡張(Data Augmentation)で多様性を確保

2. **正則化(Regularization)**
   - L1正則化(Lasso): 重み係数をゼロに近づける
   - L2正則化(Ridge): 重み係数を小さく保つ
   - Dropout: ニューラルネットワークでランダムにノードを無効化

3. **モデルの簡素化**
   - パラメータ数を減らす
   - 特徴量を削減する

4. **早期停止(Early Stopping)**
   - 検証データの誤差が増加し始めたら学習を停止

5. **クロスバリデーション**
   - K-分割交差検証で汎化性能を正確に評価

**実践例**:
```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge

# データ分割
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# L2正則化を適用
model = Ridge(alpha=1.0)  # alphaで正則化の強さを調整
model.fit(X_train, y_train)
```

過学習は機械学習の根本的な課題であり、適切な対策が不可欠です。
""",
)

Q2_GOOD_ANSWER = Answer(
    answer_id="q002_good",
    text="""
過学習は、モデルが訓練データに過剰適合して、新しいデータでの性能が悪くなることです。

**主な原因**:
- 訓練データが少なすぎる
- モデルが複雑すぎる
- ノイズを学習してしまう

**防止方法**:
1. データを増やす
2. 正則化を使う(L1/L2)
3. Dropoutを適用する
4. 早期停止で学習を止める
5. シンプルなモデルを使う

これらの方法を組み合わせて使うことで、過学習を防げます。
""",
)

# 質問3: PythonとJavaScriptの違い
Q3_ANSWER_A = Answer(
    answer_id="q003_a",
    text="""
PythonとJavaScriptの主な違い:

**実行環境**:
- Python: サーバーサイド、データ分析、AI/ML
- JavaScript: Webブラウザ、Node.jsでサーバーサイドも可能

**構文**:
- Python: インデントでブロック構造を定義
- JavaScript: 波括弧 `{}` でブロックを定義

**型システム**:
- Python: 動的型付け、型ヒント(任意)
- JavaScript: 動的型付け、TypeScriptで静的型付け可能

**用途**:
- Python: データサイエンス、機械学習、バックエンド
- JavaScript: フロントエンド開発、インタラクティブなWebアプリ

両言語とも強力ですが、使用目的に応じて選択します。
""",
)

Q3_ANSWER_B = Answer(
    answer_id="q003_b",
    text="""
PythonとJavaScriptの違いを説明します。

**Python**:
- 読みやすい構文
- データサイエンスやAIで広く使われる
- サーバーサイドアプリケーションに適している
- NumPy、Pandas、TensorFlowなどの強力なライブラリ
- インデントベースの構文

**JavaScript**:
- Web開発の標準言語
- ブラウザで直接実行可能
- Node.jsでサーバーサイドも可能
- 非同期処理が得意
- イベント駆動型プログラミング

**どちらを選ぶか**:
- Webフロントエンド → JavaScript
- データ分析・AI → Python
- フルスタック → どちらも学習推奨
""",
)

# ========================================
# データ構造の整理
# ========================================


def get_sample_question(question_id: str) -> Question:
    """質問IDからサンプル質問を取得"""
    for q in SAMPLE_QUESTIONS:
        if q.question_id == question_id:
            return q
    raise ValueError(f"質問ID {question_id} が見つかりません")


def get_sample_answer(answer_id: str) -> Answer:
    """回答IDからサンプル回答を取得"""
    all_answers = {
        "q001_excellent": Q1_EXCELLENT_ANSWER,
        "q001_good": Q1_GOOD_ANSWER,
        "q001_medium": Q1_MEDIUM_ANSWER,
        "q001_poor": Q1_POOR_ANSWER,
        "q002_excellent": Q2_EXCELLENT_ANSWER,
        "q002_good": Q2_GOOD_ANSWER,
        "q003_a": Q3_ANSWER_A,
        "q003_b": Q3_ANSWER_B,
    }
    if answer_id not in all_answers:
        raise ValueError(f"回答ID {answer_id} が見つかりません")
    return all_answers[answer_id]
