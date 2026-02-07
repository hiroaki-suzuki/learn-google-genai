"""evaluator.pyの単体テスト"""

from unittest.mock import MagicMock, patch

import pytest
from google.genai.errors import APIError, ClientError, ServerError

from movie_metadata.evaluator import MetadataEvaluator
from movie_metadata.models import (
    MetadataEvaluationOutput,
    MetadataFieldScore,
    MovieMetadata,
)


@pytest.fixture
def sample_evaluation_output_pass() -> MetadataEvaluationOutput:
    """すべてのフィールドが3.5以上（pass）の評価結果"""
    return MetadataEvaluationOutput(
        field_scores=[
            MetadataFieldScore(
                field_name="japanese_titles",
                score=4.5,
                reasoning="正確な日本語タイトルが記載されている",
            ),
            MetadataFieldScore(
                field_name="distributor", score=4.0, reasoning="配給会社が正確である"
            ),
            MetadataFieldScore(
                field_name="box_office", score=3.8, reasoning="興行収入の記載が適切である"
            ),
            MetadataFieldScore(field_name="cast", score=4.2, reasoning="主要キャストが網羅されている"),
            MetadataFieldScore(
                field_name="music", score=3.9, reasoning="音楽担当者が正確に記載されている"
            ),
        ],
        improvement_suggestions="改善の必要なし",
    )


@pytest.fixture
def sample_evaluation_output_fail() -> MetadataEvaluationOutput:
    """1つ以上のフィールドが3.5未満（fail）の評価結果"""
    return MetadataEvaluationOutput(
        field_scores=[
            MetadataFieldScore(
                field_name="japanese_titles", score=3.0, reasoning="日本語タイトルが不足している"
            ),
            MetadataFieldScore(
                field_name="distributor", score=2.5, reasoning="配給会社の情報が不正確である"
            ),
            MetadataFieldScore(
                field_name="box_office", score=3.8, reasoning="興行収入の記載が適切である"
            ),
            MetadataFieldScore(field_name="cast", score=4.0, reasoning="主要キャストが網羅されている"),
            MetadataFieldScore(
                field_name="music", score=3.5, reasoning="音楽担当者が正確に記載されている"
            ),
        ],
        improvement_suggestions="日本語タイトルに別名表記を追加してください。配給会社の正式名称を確認してください。",
    )


def test_evaluator_initialization():
    """MetadataEvaluatorの初期化テスト"""
    evaluator = MetadataEvaluator(api_key="test_key", model_name="gemini-2.0-flash")
    assert evaluator.api_key == "test_key"
    assert evaluator.model_name == "gemini-2.0-flash"


def test_evaluate_success_pass(
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_output_pass: MetadataEvaluationOutput,
):
    """evaluate()の正常系テスト（すべてのフィールドが3.5以上でpass）"""
    evaluator = MetadataEvaluator(api_key="test_key")

    # GenAIClientをモック化
    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance

        # generate_contentの戻り値をセット（JSON文字列）
        mock_client_instance.generate_content.return_value = (
            sample_evaluation_output_pass.model_dump_json()
        )

        # 実行
        result = evaluator.evaluate(sample_movie_metadata, iteration=1)

        # 検証
        assert result.iteration == 1
        assert len(result.field_scores) == 5
        assert result.overall_status == "pass"
        assert all(score.score >= 3.5 for score in result.field_scores)
        assert result.improvement_suggestions == "改善の必要なし"


def test_evaluate_success_fail(
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_output_fail: MetadataEvaluationOutput,
):
    """evaluate()の正常系テスト（1つ以上のフィールドが3.5未満でfail）"""
    evaluator = MetadataEvaluator(api_key="test_key")

    # GenAIClientをモック化
    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance

        # generate_contentの戻り値をセット（JSON文字列）
        mock_client_instance.generate_content.return_value = (
            sample_evaluation_output_fail.model_dump_json()
        )

        # 実行
        result = evaluator.evaluate(sample_movie_metadata, iteration=2)

        # 検証
        assert result.iteration == 2
        assert len(result.field_scores) == 5
        assert result.overall_status == "fail"
        assert any(score.score < 3.5 for score in result.field_scores)
        assert "日本語タイトル" in result.improvement_suggestions


def test_evaluate_with_default_iteration(
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_output_pass: MetadataEvaluationOutput,
):
    """evaluate()のデフォルトiteration値テスト"""
    evaluator = MetadataEvaluator(api_key="test_key")

    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.return_value = (
            sample_evaluation_output_pass.model_dump_json()
        )

        # iterationを省略して実行
        result = evaluator.evaluate(sample_movie_metadata)

        # デフォルト値1が設定されていることを確認
        assert result.iteration == 1


def test_evaluate_api_client_error(sample_movie_metadata: MovieMetadata):
    """evaluate()でClientErrorが発生した場合のテスト"""
    evaluator = MetadataEvaluator(api_key="test_key")

    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = ClientError(
            code=400, response_json={"error": {"message": "Invalid request"}}
        )

        # ClientErrorが再送出されることを確認
        with pytest.raises(ClientError):
            evaluator.evaluate(sample_movie_metadata)


def test_evaluate_api_server_error(sample_movie_metadata: MovieMetadata):
    """evaluate()でServerErrorが発生した場合のテスト"""
    evaluator = MetadataEvaluator(api_key="test_key")

    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = ServerError(
            code=500, response_json={"error": {"message": "Internal server error"}}
        )

        # ServerErrorが再送出されることを確認
        with pytest.raises(ServerError):
            evaluator.evaluate(sample_movie_metadata)


def test_evaluate_api_error(sample_movie_metadata: MovieMetadata):
    """evaluate()でAPIErrorが発生した場合のテスト"""
    evaluator = MetadataEvaluator(api_key="test_key")

    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = APIError(
            code=503, response_json={"error": {"message": "Service unavailable"}}
        )

        # APIErrorが再送出されることを確認
        with pytest.raises(APIError):
            evaluator.evaluate(sample_movie_metadata)


def test_evaluate_unexpected_error(sample_movie_metadata: MovieMetadata):
    """evaluate()で予期しないエラーが発生した場合のテスト"""
    evaluator = MetadataEvaluator(api_key="test_key")

    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = RuntimeError(
            "Unexpected error"
        )

        # RuntimeErrorが再送出されることを確認
        with pytest.raises(RuntimeError):
            evaluator.evaluate(sample_movie_metadata)


def test_evaluate_boundary_score_all_exactly_3_5(sample_movie_metadata: MovieMetadata):
    """すべてのスコアがちょうど3.5の境界値テスト（pass判定）"""
    evaluator = MetadataEvaluator(api_key="test_key")

    boundary_output = MetadataEvaluationOutput(
        field_scores=[
            MetadataFieldScore(field_name="japanese_titles", score=3.5, reasoning="普通"),
            MetadataFieldScore(field_name="distributor", score=3.5, reasoning="普通"),
            MetadataFieldScore(field_name="box_office", score=3.5, reasoning="普通"),
        ],
        improvement_suggestions="改善の必要なし",
    )

    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.return_value = (
            boundary_output.model_dump_json()
        )

        result = evaluator.evaluate(sample_movie_metadata)

        # 3.5以上なのでpass判定になることを確認
        assert result.overall_status == "pass"


def test_evaluate_boundary_score_one_below_3_5(sample_movie_metadata: MovieMetadata):
    """1つのスコアが3.5未満の境界値テスト（fail判定）"""
    evaluator = MetadataEvaluator(api_key="test_key")

    boundary_output = MetadataEvaluationOutput(
        field_scores=[
            MetadataFieldScore(
                field_name="japanese_titles", score=3.49, reasoning="わずかに基準未満"
            ),
            MetadataFieldScore(field_name="distributor", score=3.5, reasoning="普通"),
            MetadataFieldScore(field_name="box_office", score=4.0, reasoning="良好"),
        ],
        improvement_suggestions="japanese_titlesを改善してください",
    )

    with patch(
        "movie_metadata.evaluator.GenAIClient"
    ) as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.return_value = (
            boundary_output.model_dump_json()
        )

        result = evaluator.evaluate(sample_movie_metadata)

        # 1つでも3.5未満ならfail判定になることを確認
        assert result.overall_status == "fail"
