"""main_refineモジュールのテスト"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import main_refine
from movie_metadata.csv_reader import CSVReader
from movie_metadata.models import (
    MetadataEvaluationResult,
    MetadataFieldScore,
    MetadataRefinementResult,
    MovieInput,
    RefinementHistoryEntry,
)


@pytest.fixture
def sample_refinement_result(sample_movie_metadata):
    """テスト用MetadataRefinementResultフィクスチャ"""
    evaluation = MetadataEvaluationResult(
        iteration=1,
        field_scores=[
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良好")
        ],
        overall_status="pass",
        improvement_suggestions="改善の必要なし",
    )
    history = [
        RefinementHistoryEntry(
            iteration=1, metadata=sample_movie_metadata, evaluation=evaluation
        )
    ]
    return MetadataRefinementResult(
        final_metadata=sample_movie_metadata,
        history=history,
        success=True,
        total_iterations=1,
    )


def test_main_refine_records_errors_and_writes_batch(
    mocker, caplog, sample_refinement_result
):
    """エラーを記録し、バッチ結果を書き出すことを確認"""
    dummy_config = SimpleNamespace(
        gemini_api_key="test",
        model_name="model",
        rate_limit_sleep=0.0,
        log_level="INFO",
        csv_path=Path("data/movies.csv"),
        output_dir=Path("data/output"),
        quality_score_threshold=3.5,
    )
    mocker.patch("main_refine.AppConfig", return_value=dummy_config)
    mocker.patch("main_refine.setup_logging")

    movies = [
        MovieInput(title="Movie A", release_date="2024-01-01", country="Japan"),
        MovieInput(title="Movie B", release_date="2024-01-02", country="Japan"),
    ]
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.read.return_value = movies
    mocker.patch("main_refine.CSVReader", return_value=mock_csv_reader)

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.side_effect = [sample_refinement_result, RuntimeError("boom")]
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    mock_writer = mocker.MagicMock()
    mocker.patch("main_refine.RefinementResultWriter", return_value=mock_writer)

    with caplog.at_level("ERROR"):
        main_refine.main()

    assert mock_writer.write_batch.call_count == 1
    batch_result, output_dir = mock_writer.write_batch.call_args.args
    assert batch_result.total_count == 2
    assert batch_result.success_count == 1
    assert batch_result.error_count == 1
    assert batch_result.errors == [{"title": "Movie B", "message": "boom"}]
    expected_output_dir = Path(main_refine.__file__).parent / dummy_config.output_dir
    assert output_dir == expected_output_dir

    assert "エラー件数: 1" in caplog.text
    assert "エラーが発生した映画: Movie B" in caplog.text


def test_main_refine_continues_after_error(mocker, sample_movie_metadata):
    """エラー後も処理が継続されることを確認"""
    dummy_config = SimpleNamespace(
        gemini_api_key="test",
        model_name="model",
        rate_limit_sleep=0.0,
        log_level="INFO",
        csv_path=Path("data/movies.csv"),
        output_dir=Path("data/output"),
        quality_score_threshold=3.5,
    )
    mocker.patch("main_refine.AppConfig", return_value=dummy_config)
    mocker.patch("main_refine.setup_logging")

    movies = [
        MovieInput(title="Movie A", release_date="2024-01-01", country="Japan"),
        MovieInput(title="Unknown", release_date="2024-01-02", country="Japan"),
        MovieInput(title="Movie C", release_date="2024-01-03", country="Japan"),
    ]
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.read.return_value = movies
    mocker.patch("main_refine.CSVReader", return_value=mock_csv_reader)

    def build_result(title: str) -> MetadataRefinementResult:
        metadata = sample_movie_metadata.model_copy(update={"title": title})
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=[
                MetadataFieldScore(field_name="title", score=4.0, reasoning="良好")
            ],
            overall_status="pass",
            improvement_suggestions="改善の必要なし",
        )
        history = [
            RefinementHistoryEntry(
                iteration=1, metadata=metadata, evaluation=evaluation
            )
        ]
        return MetadataRefinementResult(
            final_metadata=metadata,
            history=history,
            success=True,
            total_iterations=1,
        )

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.side_effect = [
        build_result("Movie A"),
        RuntimeError("not found"),
        build_result("Movie C"),
    ]
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    mock_writer = mocker.MagicMock()
    mocker.patch("main_refine.RefinementResultWriter", return_value=mock_writer)

    main_refine.main()

    assert mock_refiner.refine.call_count == 3
    batch_result, _ = mock_writer.write_batch.call_args.args
    assert batch_result.total_count == 3
    assert batch_result.success_count == 2
    assert batch_result.error_count == 1
    assert batch_result.errors == [{"title": "Unknown", "message": "not found"}]
    assert len(batch_result.results) == 2
    titles = {result.final_metadata.title for result in batch_result.results}
    assert titles == {"Movie A", "Movie C"}


def test_main_refine_logs_error_summary_for_multiple_errors(mocker, caplog):
    """複数エラー時にエラーサマリーが出力されることを確認"""
    dummy_config = SimpleNamespace(
        gemini_api_key="test",
        model_name="model",
        rate_limit_sleep=0.0,
        log_level="INFO",
        csv_path=Path("data/movies.csv"),
        output_dir=Path("data/output"),
        quality_score_threshold=3.5,
    )
    mocker.patch("main_refine.AppConfig", return_value=dummy_config)
    mocker.patch("main_refine.setup_logging")

    movies = [
        MovieInput(title="Movie A", release_date="2024-01-01", country="Japan"),
        MovieInput(title="Movie B", release_date="2024-01-02", country="Japan"),
    ]
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.read.return_value = movies
    mocker.patch("main_refine.CSVReader", return_value=mock_csv_reader)

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.side_effect = [RuntimeError("boom"), RuntimeError("boom")]
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    mock_writer = mocker.MagicMock()
    mocker.patch("main_refine.RefinementResultWriter", return_value=mock_writer)

    with caplog.at_level("ERROR"):
        main_refine.main()

    assert "エラー件数: 2" in caplog.text
    assert "エラーが発生した映画: Movie A, Movie B" in caplog.text


def test_main_refine_logs_progress_for_each_record(
    mocker, caplog, sample_refinement_result
):
    """進捗ログがレコードごとに出力されることを確認"""
    dummy_config = SimpleNamespace(
        gemini_api_key="test",
        model_name="model",
        rate_limit_sleep=0.0,
        log_level="INFO",
        csv_path=Path("data/movies.csv"),
        output_dir=Path("data/output"),
        quality_score_threshold=3.5,
    )
    mocker.patch("main_refine.AppConfig", return_value=dummy_config)
    mocker.patch("main_refine.setup_logging")

    movies = [
        MovieInput(title="Movie A", release_date="2024-01-01", country="Japan"),
        MovieInput(title="Movie B", release_date="2024-01-02", country="Japan"),
    ]
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.read.return_value = movies
    mocker.patch("main_refine.CSVReader", return_value=mock_csv_reader)

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.return_value = sample_refinement_result
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    mock_writer = mocker.MagicMock()
    mocker.patch("main_refine.RefinementResultWriter", return_value=mock_writer)

    with caplog.at_level("INFO"):
        main_refine.main()

    assert "処理中: 1/2件完了（タイトル: Movie A）" in caplog.text
    assert "処理中: 2/2件完了（タイトル: Movie B）" in caplog.text


def test_main_refine_uses_csv_filename_env(
    monkeypatch, mocker, sample_refinement_result
):
    """CSV_FILENAME環境変数が読み込まれることを確認"""
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setenv("CSV_FILENAME", "movies_test.csv")
    mocker.patch("main_refine.setup_logging")

    movies = [MovieInput(title="Movie A", release_date="2024-01-01", country="Japan")]
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.read.return_value = movies
    mocker.patch("main_refine.CSVReader", return_value=mock_csv_reader)

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.return_value = sample_refinement_result
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    mock_writer = mocker.MagicMock()
    mocker.patch("main_refine.RefinementResultWriter", return_value=mock_writer)

    main_refine.main()

    expected_csv_path = Path(main_refine.__file__).parent / Path("data/movies_test.csv")
    assert mock_csv_reader.read.call_args.args[0] == expected_csv_path


def test_main_refine_processes_all_records_in_movies_csv(
    mocker, sample_refinement_result
):
    """movies.csvの全レコードが処理されることを確認"""
    csv_path = Path(main_refine.__file__).parent / Path("data/movies.csv")
    expected_count = len(CSVReader().read(csv_path))
    assert expected_count > 1

    dummy_config = SimpleNamespace(
        gemini_api_key="test",
        model_name="model",
        rate_limit_sleep=0.0,
        log_level="INFO",
        csv_path=Path("data/movies.csv"),
        output_dir=Path("data/output"),
        quality_score_threshold=3.5,
    )
    mocker.patch("main_refine.AppConfig", return_value=dummy_config)
    mocker.patch("main_refine.setup_logging")

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.return_value = sample_refinement_result
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    mock_writer = mocker.MagicMock()
    mocker.patch("main_refine.RefinementResultWriter", return_value=mock_writer)

    main_refine.main()

    assert mock_refiner.refine.call_count == expected_count
    assert mock_writer.write_batch.call_count == 1


def test_main_refine_writes_timestamped_batch_file(
    tmp_path, monkeypatch, mocker, sample_refinement_result
):
    """タイムスタンプ付きのバッチ結果ファイルが生成されることを確認"""
    dummy_config = SimpleNamespace(
        gemini_api_key="test",
        model_name="model",
        rate_limit_sleep=0.0,
        log_level="INFO",
        csv_path=Path("data/movies.csv"),
        output_dir=tmp_path,
    )
    mocker.patch("main_refine.AppConfig", return_value=dummy_config)
    mocker.patch("main_refine.setup_logging")

    movies = [MovieInput(title="Movie A", release_date="2024-01-01", country="Japan")]
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.read.return_value = movies
    mocker.patch("main_refine.CSVReader", return_value=mock_csv_reader)

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.return_value = sample_refinement_result
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    from datetime import datetime as real_datetime

    class FixedDateTime:
        @classmethod
        def now(cls):
            return real_datetime(2026, 2, 7, 14, 30, 25)

    monkeypatch.setattr(
        "movie_metadata.refinement_writer.datetime",
        FixedDateTime,
    )

    main_refine.main()

    expected_file = tmp_path / "batch_refinement_result_20260207_143025.json"
    assert expected_file.exists()


def test_main_refine_batch_json_contains_all_results(
    tmp_path, monkeypatch, mocker, sample_movie_metadata
):
    """生成されたJSONに全レコードの結果が含まれることを確認"""
    dummy_config = SimpleNamespace(
        gemini_api_key="test",
        model_name="model",
        rate_limit_sleep=0.0,
        log_level="INFO",
        csv_path=Path("data/movies.csv"),
        output_dir=tmp_path,
    )
    mocker.patch("main_refine.AppConfig", return_value=dummy_config)
    mocker.patch("main_refine.setup_logging")

    movies = [
        MovieInput(title="Movie A", release_date="2024-01-01", country="Japan"),
        MovieInput(title="Movie B", release_date="2024-01-02", country="Japan"),
    ]
    mock_csv_reader = mocker.MagicMock()
    mock_csv_reader.read.return_value = movies
    mocker.patch("main_refine.CSVReader", return_value=mock_csv_reader)

    def build_result(title: str) -> MetadataRefinementResult:
        metadata = sample_movie_metadata.model_copy(update={"title": title})
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=[
                MetadataFieldScore(field_name="title", score=4.0, reasoning="良好")
            ],
            overall_status="pass",
            improvement_suggestions="改善の必要なし",
        )
        history = [
            RefinementHistoryEntry(
                iteration=1, metadata=metadata, evaluation=evaluation
            )
        ]
        return MetadataRefinementResult(
            final_metadata=metadata,
            history=history,
            success=True,
            total_iterations=1,
        )

    mock_refiner = mocker.MagicMock()
    mock_refiner.refine.side_effect = [build_result("Movie A"), build_result("Movie B")]
    mocker.patch("main_refine.MetadataRefiner", return_value=mock_refiner)

    from datetime import datetime as real_datetime

    class FixedDateTime:
        @classmethod
        def now(cls):
            return real_datetime(2026, 2, 7, 14, 30, 25)

    monkeypatch.setattr(
        "movie_metadata.refinement_writer.datetime",
        FixedDateTime,
    )

    main_refine.main()

    output_file = tmp_path / "batch_refinement_result_20260207_143025.json"
    assert output_file.exists()

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(data["results"]) == len(movies)
    titles = {result["final_metadata"]["title"] for result in data["results"]}
    assert titles == {"Movie A", "Movie B"}
