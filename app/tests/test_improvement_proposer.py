"""improvement_proposer.pyの単体テスト"""

from unittest.mock import MagicMock, patch

import pytest
from google.genai.errors import APIError, ClientError, ServerError

from movie_metadata.improvement_proposer import ImprovementProposer
from movie_metadata.models import (
    MetadataEvaluationResult,
    MetadataFieldScore,
    MovieInput,
    MovieMetadata,
)


@pytest.fixture
def sample_evaluation_result_pass() -> MetadataEvaluationResult:
    """すべてのフィールドが閾値以上（pass）の評価結果"""
    return MetadataEvaluationResult(
        iteration=1,
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
                field_name="box_office",
                score=3.8,
                reasoning="興行収入の記載が適切である",
            ),
        ],
        overall_status="pass",
        improvement_suggestions="改善の必要なし",
    )


@pytest.fixture
def sample_evaluation_result_fail() -> MetadataEvaluationResult:
    """1つ以上のフィールドが閾値未満（fail）の評価結果"""
    return MetadataEvaluationResult(
        iteration=2,
        field_scores=[
            MetadataFieldScore(
                field_name="japanese_titles",
                score=3.0,
                reasoning="日本語タイトルが不足している",
            ),
            MetadataFieldScore(
                field_name="distributor",
                score=2.5,
                reasoning="配給会社の情報が不正確である",
            ),
            MetadataFieldScore(
                field_name="box_office",
                score=3.8,
                reasoning="興行収入の記載が適切である",
            ),
        ],
        overall_status="fail",
        improvement_suggestions="日本語タイトルに別名表記を追加してください。配給会社の正式名称を確認してください。",
    )


def test_proposer_initialization():
    """ImprovementProposerの初期化テスト"""
    proposer = ImprovementProposer(
        api_key="test_key", model_name="gemini-2.0-flash", threshold=3.5
    )
    assert proposer.api_key == "test_key"
    assert proposer.model_name == "gemini-2.0-flash"
    assert proposer.threshold == 3.5


def test_propose_pass_status(
    sample_movie_input: MovieInput,
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_result_pass: MetadataEvaluationResult,
):
    """propose()の正常系テスト（overall_status="pass"で改善不要を返す）"""
    proposer = ImprovementProposer(api_key="test_key")

    # overall_status="pass"の場合、API呼び出しなしで"改善の必要なし"を返す
    result = proposer.propose(
        movie_input=sample_movie_input,
        current_metadata=sample_movie_metadata,
        evaluation=sample_evaluation_result_pass,
    )

    assert result == "改善の必要なし"


def test_propose_fail_status(
    sample_movie_input: MovieInput,
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_result_fail: MetadataEvaluationResult,
):
    """propose()の正常系テスト（overall_status="fail"で改善提案を生成する）"""
    proposer = ImprovementProposer(api_key="test_key")

    # GenAIClientをモック化
    with patch("movie_metadata.improvement_proposer.GenAIClient") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance

        # generate_contentの戻り値をセット
        mock_proposal = (
            "日本語タイトルに『Test Movie』の別名表記を追加してください。\n"
            "配給会社の正式名称を確認し、『テスト配給株式会社』と記載してください。"
        )
        mock_client_instance.generate_content.return_value = mock_proposal

        # 実行
        result = proposer.propose(
            movie_input=sample_movie_input,
            current_metadata=sample_movie_metadata,
            evaluation=sample_evaluation_result_fail,
        )

        # 検証
        assert "日本語タイトル" in result
        assert "配給会社" in result
        mock_client_instance.generate_content.assert_called_once()


def test_propose_api_client_error(
    sample_movie_input: MovieInput,
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_result_fail: MetadataEvaluationResult,
):
    """propose()でClientErrorが発生した場合のテスト"""
    proposer = ImprovementProposer(api_key="test_key")

    with patch("movie_metadata.improvement_proposer.GenAIClient") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = ClientError(
            code=400, response_json={"error": {"message": "Invalid request"}}
        )

        # ClientErrorが再送出されることを確認
        with pytest.raises(ClientError):
            proposer.propose(
                movie_input=sample_movie_input,
                current_metadata=sample_movie_metadata,
                evaluation=sample_evaluation_result_fail,
            )


def test_propose_api_server_error(
    sample_movie_input: MovieInput,
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_result_fail: MetadataEvaluationResult,
):
    """propose()でServerErrorが発生した場合のテスト"""
    proposer = ImprovementProposer(api_key="test_key")

    with patch("movie_metadata.improvement_proposer.GenAIClient") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = ServerError(
            code=500, response_json={"error": {"message": "Internal server error"}}
        )

        # ServerErrorが再送出されることを確認
        with pytest.raises(ServerError):
            proposer.propose(
                movie_input=sample_movie_input,
                current_metadata=sample_movie_metadata,
                evaluation=sample_evaluation_result_fail,
            )


def test_propose_api_error(
    sample_movie_input: MovieInput,
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_result_fail: MetadataEvaluationResult,
):
    """propose()でAPIErrorが発生した場合のテスト"""
    proposer = ImprovementProposer(api_key="test_key")

    with patch("movie_metadata.improvement_proposer.GenAIClient") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = APIError(
            code=503, response_json={"error": {"message": "Service unavailable"}}
        )

        # APIErrorが再送出されることを確認
        with pytest.raises(APIError):
            proposer.propose(
                movie_input=sample_movie_input,
                current_metadata=sample_movie_metadata,
                evaluation=sample_evaluation_result_fail,
            )


def test_propose_unexpected_error(
    sample_movie_input: MovieInput,
    sample_movie_metadata: MovieMetadata,
    sample_evaluation_result_fail: MetadataEvaluationResult,
):
    """propose()で予期しないエラーが発生した場合のテスト"""
    proposer = ImprovementProposer(api_key="test_key")

    with patch("movie_metadata.improvement_proposer.GenAIClient") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        mock_client_instance.generate_content.side_effect = RuntimeError(
            "Unexpected error"
        )

        # RuntimeErrorが再送出されることを確認
        with pytest.raises(RuntimeError):
            proposer.propose(
                movie_input=sample_movie_input,
                current_metadata=sample_movie_metadata,
                evaluation=sample_evaluation_result_fail,
            )
