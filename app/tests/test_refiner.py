"""refinement_loopモジュールのテスト"""

from unittest.mock import MagicMock

import pytest
from google.genai.errors import APIError, ClientError, ServerError

from movie_metadata.models import (
    MetadataEvaluationResult,
    MetadataFieldScore,
    MovieInput,
    MovieMetadata,
)
from movie_metadata.refiner import MetadataRefiner


@pytest.fixture
def sample_movie_input() -> MovieInput:
    """テスト用MovieInputフィクスチャ"""
    return MovieInput(title="Test Movie", release_date="2024-01-01", country="Japan")


@pytest.fixture
def sample_movie_metadata() -> MovieMetadata:
    """テスト用MovieMetadataフィクスチャ"""
    return MovieMetadata(
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


@pytest.fixture
def passing_evaluation() -> MetadataEvaluationResult:
    """pass判定のMetadataEvaluationResultフィクスチャ"""
    return MetadataEvaluationResult(
        iteration=1,
        field_scores=[
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良好"),
            MetadataFieldScore(field_name="cast", score=4.5, reasoning="良好"),
        ],
        overall_status="pass",
        improvement_suggestions="改善の必要なし",
    )


@pytest.fixture
def failing_evaluation() -> MetadataEvaluationResult:
    """fail判定のMetadataEvaluationResultフィクスチャ"""
    return MetadataEvaluationResult(
        iteration=1,
        field_scores=[
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良好"),
            MetadataFieldScore(field_name="cast", score=2.5, reasoning="改善が必要"),
        ],
        overall_status="fail",
        improvement_suggestions="キャスト情報を補完してください",
    )


def test_refiner_initialization(mocker):
    """MetadataRefinerの初期化テスト"""
    # GenAIClientのモックをパッチ
    MagicMock()
    mocker.patch("movie_metadata.refiner.MetadataEvaluator.__init__", return_value=None)
    mocker.patch(
        "movie_metadata.refiner.ImprovementProposer.__init__", return_value=None
    )

    refiner = MetadataRefiner(
        api_key="test_api_key", model_name="gemini-2.0-flash", rate_limit_sleep=0.5
    )

    assert refiner.api_key == "test_api_key"
    assert refiner.model_name == "gemini-2.0-flash"
    assert refiner.rate_limit_sleep == 0.5


def test_refine_success_first_iteration(
    mocker, sample_movie_input, sample_movie_metadata, passing_evaluation
):
    """初回イテレーションで成功するテスト"""
    # GenAIClientのコンテキストマネージャーをモック化
    mock_client = MagicMock()
    mock_genai_client_class = mocker.patch("movie_metadata.refiner.GenAIClient")
    mock_genai_client_class.return_value.__enter__.return_value = mock_client
    mock_genai_client_class.return_value.__exit__.return_value = None

    # MovieMetadataFetcherをモック化
    mock_fetcher_class = mocker.patch("movie_metadata.refiner.MovieMetadataFetcher")
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = sample_movie_metadata
    mock_fetcher_class.return_value = mock_fetcher

    # MetadataEvaluatorをモック化
    mock_evaluator = MagicMock()
    mock_evaluator.evaluate.return_value = passing_evaluation
    mocker.patch(
        "movie_metadata.refiner.MetadataEvaluator", return_value=mock_evaluator
    )

    # ImprovementProposerをモック化
    mock_proposer = MagicMock()
    mocker.patch(
        "movie_metadata.refiner.ImprovementProposer", return_value=mock_proposer
    )

    # time.sleepをモック化してテストを高速化
    mocker.patch("movie_metadata.refiner.time.sleep")

    # テスト実行
    refiner = MetadataRefiner(api_key="test_api_key", rate_limit_sleep=0.0)
    result = refiner.refine(sample_movie_input, max_iterations=3, threshold=3.5)

    # 検証
    assert result.success is True
    assert result.total_iterations == 1
    assert result.final_metadata == sample_movie_metadata
    assert len(result.history) == 1
    assert result.history[0].iteration == 1
    assert result.history[0].metadata == sample_movie_metadata
    assert result.history[0].evaluation == passing_evaluation

    # fetchが1回だけ呼ばれたことを確認
    mock_fetcher.fetch.assert_called_once_with(sample_movie_input)
    mock_fetcher.fetch_with_improvement.assert_not_called()

    # evaluateが1回だけ呼ばれたことを確認
    mock_evaluator.evaluate.assert_called_once_with(sample_movie_metadata, 1)

    # proposeは呼ばれないことを確認（初回で成功したため）
    mock_proposer.propose.assert_not_called()


def test_refine_success_second_iteration(
    mocker, sample_movie_input, sample_movie_metadata, failing_evaluation
):
    """2回目のイテレーションで成功するテスト"""
    # GenAIClientのコンテキストマネージャーをモック化
    mock_client = MagicMock()
    mock_genai_client_class = mocker.patch("movie_metadata.refiner.GenAIClient")
    mock_genai_client_class.return_value.__enter__.return_value = mock_client
    mock_genai_client_class.return_value.__exit__.return_value = None

    # 2回目の評価結果（pass）を作成
    passing_evaluation_iter2 = MetadataEvaluationResult(
        iteration=2,
        field_scores=[
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良好"),
            MetadataFieldScore(field_name="cast", score=4.5, reasoning="改善された"),
        ],
        overall_status="pass",
        improvement_suggestions="改善の必要なし",
    )

    # MovieMetadataFetcherをモック化
    mock_fetcher_class = mocker.patch("movie_metadata.refiner.MovieMetadataFetcher")
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = sample_movie_metadata
    mock_fetcher.fetch_with_improvement.return_value = sample_movie_metadata
    mock_fetcher_class.return_value = mock_fetcher

    # MetadataEvaluatorをモック化
    mock_evaluator = MagicMock()
    # 1回目はfail、2回目はpassを返す
    mock_evaluator.evaluate.side_effect = [failing_evaluation, passing_evaluation_iter2]
    mocker.patch(
        "movie_metadata.refiner.MetadataEvaluator", return_value=mock_evaluator
    )

    # ImprovementProposerをモック化
    mock_proposer = MagicMock()
    mock_proposer.propose.return_value = "キャスト情報を補完してください"
    mocker.patch(
        "movie_metadata.refiner.ImprovementProposer", return_value=mock_proposer
    )

    # time.sleepをモック化してテストを高速化
    mocker.patch("movie_metadata.refiner.time.sleep")

    # テスト実行
    refiner = MetadataRefiner(api_key="test_api_key", rate_limit_sleep=0.0)
    result = refiner.refine(sample_movie_input, max_iterations=3, threshold=3.5)

    # 検証
    assert result.success is True
    assert result.total_iterations == 2
    assert result.final_metadata == sample_movie_metadata
    assert len(result.history) == 2

    # fetchが1回、fetch_with_improvementが1回呼ばれたことを確認
    mock_fetcher.fetch.assert_called_once_with(sample_movie_input)
    assert mock_fetcher.fetch_with_improvement.call_count == 1

    # evaluateが2回呼ばれたことを確認
    assert mock_evaluator.evaluate.call_count == 2

    # proposeが1回呼ばれたことを確認（1回目のfail後）
    mock_proposer.propose.assert_called_once()


def test_refine_failure_max_iterations(
    mocker, sample_movie_input, sample_movie_metadata, failing_evaluation
):
    """最大イテレーション数に達して失敗するテスト"""
    # GenAIClientのコンテキストマネージャーをモック化
    mock_client = MagicMock()
    mock_genai_client_class = mocker.patch("movie_metadata.refiner.GenAIClient")
    mock_genai_client_class.return_value.__enter__.return_value = mock_client
    mock_genai_client_class.return_value.__exit__.return_value = None

    # MovieMetadataFetcherをモック化
    mock_fetcher_class = mocker.patch("movie_metadata.refiner.MovieMetadataFetcher")
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = sample_movie_metadata
    mock_fetcher.fetch_with_improvement.return_value = sample_movie_metadata
    mock_fetcher_class.return_value = mock_fetcher

    # MetadataEvaluatorをモック化（すべてfailを返す）
    mock_evaluator = MagicMock()
    failing_evaluation_iter1 = MetadataEvaluationResult(
        iteration=1,
        field_scores=[
            MetadataFieldScore(field_name="cast", score=2.5, reasoning="改善が必要"),
        ],
        overall_status="fail",
        improvement_suggestions="キャスト情報を補完してください",
    )
    failing_evaluation_iter2 = MetadataEvaluationResult(
        iteration=2,
        field_scores=[
            MetadataFieldScore(
                field_name="cast", score=2.8, reasoning="まだ改善が必要"
            ),
        ],
        overall_status="fail",
        improvement_suggestions="さらにキャスト情報を補完してください",
    )
    failing_evaluation_iter3 = MetadataEvaluationResult(
        iteration=3,
        field_scores=[
            MetadataFieldScore(field_name="cast", score=3.0, reasoning="まだ不十分"),
        ],
        overall_status="fail",
        improvement_suggestions="キャスト情報を再度補完してください",
    )
    mock_evaluator.evaluate.side_effect = [
        failing_evaluation_iter1,
        failing_evaluation_iter2,
        failing_evaluation_iter3,
    ]
    mocker.patch(
        "movie_metadata.refiner.MetadataEvaluator", return_value=mock_evaluator
    )

    # ImprovementProposerをモック化
    mock_proposer = MagicMock()
    mocker.patch(
        "movie_metadata.refiner.ImprovementProposer", return_value=mock_proposer
    )

    # time.sleepをモック化してテストを高速化
    mocker.patch("movie_metadata.refiner.time.sleep")

    # テスト実行
    refiner = MetadataRefiner(api_key="test_api_key", rate_limit_sleep=0.0)
    result = refiner.refine(sample_movie_input, max_iterations=3, threshold=3.5)

    # 検証
    assert result.success is False
    assert result.total_iterations == 3
    assert result.final_metadata == sample_movie_metadata
    assert len(result.history) == 3

    # fetchが1回、fetch_with_improvementが2回呼ばれたことを確認
    mock_fetcher.fetch.assert_called_once()
    assert mock_fetcher.fetch_with_improvement.call_count == 2

    # evaluateが3回呼ばれたことを確認
    assert mock_evaluator.evaluate.call_count == 3

    # proposeが2回呼ばれたことを確認（最終イテレーション後は呼ばれない）
    assert mock_proposer.propose.call_count == 2


def test_refine_api_error_client_error(mocker, sample_movie_input):
    """ClientErrorが発生した場合のテスト"""
    # GenAIClientのコンテキストマネージャーをモック化
    mock_client = MagicMock()
    mock_genai_client_class = mocker.patch("movie_metadata.refiner.GenAIClient")
    mock_genai_client_class.return_value.__enter__.return_value = mock_client
    mock_genai_client_class.return_value.__exit__.return_value = None

    # MovieMetadataFetcherをモック化してClientErrorを発生させる
    mock_fetcher_class = mocker.patch("movie_metadata.refiner.MovieMetadataFetcher")
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.side_effect = ClientError(
        code=400, response_json={"error": {"message": "Invalid request"}}
    )
    mock_fetcher_class.return_value = mock_fetcher

    # MetadataEvaluatorとImprovementProposerをモック化
    mocker.patch("movie_metadata.refiner.MetadataEvaluator", return_value=MagicMock())
    mocker.patch("movie_metadata.refiner.ImprovementProposer", return_value=MagicMock())

    # time.sleepをモック化してテストを高速化
    mocker.patch("movie_metadata.refiner.time.sleep")

    # テスト実行
    refiner = MetadataRefiner(api_key="test_api_key", rate_limit_sleep=0.0)

    with pytest.raises(ClientError) as exc_info:
        refiner.refine(sample_movie_input, max_iterations=3, threshold=3.5)

    assert "Invalid request" in str(exc_info.value)


def test_refine_api_error_server_error(mocker, sample_movie_input):
    """ServerErrorが発生した場合のテスト"""
    # GenAIClientのコンテキストマネージャーをモック化
    mock_client = MagicMock()
    mock_genai_client_class = mocker.patch("movie_metadata.refiner.GenAIClient")
    mock_genai_client_class.return_value.__enter__.return_value = mock_client
    mock_genai_client_class.return_value.__exit__.return_value = None

    # MovieMetadataFetcherをモック化してServerErrorを発生させる
    mock_fetcher_class = mocker.patch("movie_metadata.refiner.MovieMetadataFetcher")
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.side_effect = ServerError(
        code=500, response_json={"error": {"message": "Internal server error"}}
    )
    mock_fetcher_class.return_value = mock_fetcher

    # MetadataEvaluatorとImprovementProposerをモック化
    mocker.patch("movie_metadata.refiner.MetadataEvaluator", return_value=MagicMock())
    mocker.patch("movie_metadata.refiner.ImprovementProposer", return_value=MagicMock())

    # time.sleepをモック化してテストを高速化
    mocker.patch("movie_metadata.refiner.time.sleep")

    # テスト実行
    refiner = MetadataRefiner(api_key="test_api_key", rate_limit_sleep=0.0)

    with pytest.raises(ServerError) as exc_info:
        refiner.refine(sample_movie_input, max_iterations=3, threshold=3.5)

    assert "Internal server error" in str(exc_info.value)


def test_refine_api_error_generic_api_error(mocker, sample_movie_input):
    """APIErrorが発生した場合のテスト"""
    # GenAIClientのコンテキストマネージャーをモック化
    mock_client = MagicMock()
    mock_genai_client_class = mocker.patch("movie_metadata.refiner.GenAIClient")
    mock_genai_client_class.return_value.__enter__.return_value = mock_client
    mock_genai_client_class.return_value.__exit__.return_value = None

    # MovieMetadataFetcherをモック化してAPIErrorを発生させる
    mock_fetcher_class = mocker.patch("movie_metadata.refiner.MovieMetadataFetcher")
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.side_effect = APIError(
        code=429, response_json={"error": {"message": "Rate limit exceeded"}}
    )
    mock_fetcher_class.return_value = mock_fetcher

    # MetadataEvaluatorとImprovementProposerをモック化
    mocker.patch("movie_metadata.refiner.MetadataEvaluator", return_value=MagicMock())
    mocker.patch("movie_metadata.refiner.ImprovementProposer", return_value=MagicMock())

    # time.sleepをモック化してテストを高速化
    mocker.patch("movie_metadata.refiner.time.sleep")

    # テスト実行
    refiner = MetadataRefiner(api_key="test_api_key", rate_limit_sleep=0.0)

    with pytest.raises(APIError) as exc_info:
        refiner.refine(sample_movie_input, max_iterations=3, threshold=3.5)

    assert "Rate limit exceeded" in str(exc_info.value)


def test_refine_evaluator_api_error(mocker, sample_movie_input, sample_movie_metadata):
    """Evaluatorでエラーが発生した場合のテスト"""
    # GenAIClientのコンテキストマネージャーをモック化
    mock_client = MagicMock()
    mock_genai_client_class = mocker.patch("movie_metadata.refiner.GenAIClient")
    mock_genai_client_class.return_value.__enter__.return_value = mock_client
    mock_genai_client_class.return_value.__exit__.return_value = None

    # MovieMetadataFetcherをモック化
    mock_fetcher_class = mocker.patch("movie_metadata.refiner.MovieMetadataFetcher")
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = sample_movie_metadata
    mock_fetcher_class.return_value = mock_fetcher

    # MetadataEvaluatorをモック化してServerErrorを発生させる
    mock_evaluator = MagicMock()
    mock_evaluator.evaluate.side_effect = ServerError(
        code=503, response_json={"error": {"message": "Service unavailable"}}
    )
    mocker.patch(
        "movie_metadata.refiner.MetadataEvaluator", return_value=mock_evaluator
    )

    # ImprovementProposerをモック化
    mocker.patch("movie_metadata.refiner.ImprovementProposer", return_value=MagicMock())

    # time.sleepをモック化してテストを高速化
    mocker.patch("movie_metadata.refiner.time.sleep")

    # テスト実行
    refiner = MetadataRefiner(api_key="test_api_key", rate_limit_sleep=0.0)

    with pytest.raises(ServerError) as exc_info:
        refiner.refine(sample_movie_input, max_iterations=3, threshold=3.5)

    assert "Service unavailable" in str(exc_info.value)
