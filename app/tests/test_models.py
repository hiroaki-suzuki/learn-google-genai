"""models.pyのPydanticモデルのバリデーションテスト"""

import pytest
from pydantic import ValidationError

from movie_metadata.models import (
    BatchRefinementResult,
    MetadataEvaluationOutput,
    MetadataEvaluationResult,
    MetadataFieldScore,
    MetadataRefinementResult,
    MovieInput,
    MovieMetadata,
    RefinementHistoryEntry,
)


class TestMovieInput:
    """MovieInputモデルのテスト"""

    def test_valid_movie_input(self) -> None:
        """正常系: 有効なMovieInputを作成"""
        movie = MovieInput(
            title="Test Movie", release_date="2024-01-01", country="Japan"
        )
        assert movie.title == "Test Movie"
        assert movie.release_date == "2024-01-01"
        assert movie.country == "Japan"

    def test_movie_input_with_missing_field(self) -> None:
        """異常系: 必須フィールドが欠けている場合"""
        with pytest.raises(ValidationError):
            MovieInput(title="Test Movie", release_date="2024-01-01")  # type: ignore


class TestMovieMetadata:
    """MovieMetadataモデルのテスト"""

    def test_valid_movie_metadata(self) -> None:
        """正常系: 有効なMovieMetadataを作成"""
        metadata = MovieMetadata(
            title="Test Movie",
            japanese_titles=["テスト映画"],
            original_work="原作作品",
            original_authors=["原作者A"],
            release_date="2024-01-01",
            country="Japan",
            distributor="配給会社A",
            production_companies=["制作会社A"],
            box_office="$100M",
            cast=["俳優A", "俳優B"],
            screenwriters=["脚本家A"],
            music=["作曲家C"],
            voice_actors=["声優D"],
        )
        assert metadata.title == "Test Movie"
        assert metadata.japanese_titles == ["テスト映画"]
        assert len(metadata.cast) == 2

    def test_movie_metadata_empty_lists(self) -> None:
        """正常系: 空のリストを許容する"""
        metadata = MovieMetadata(
            title="Test Movie",
            japanese_titles=[],
            original_work="情報なし",
            original_authors=[],
            release_date="2024-01-01",
            country="Japan",
            distributor="情報なし",
            production_companies=[],
            box_office="情報なし",
            cast=[],
            screenwriters=[],
            music=[],
            voice_actors=[],
        )
        assert metadata.japanese_titles == []
        assert metadata.cast == []

    def test_movie_metadata_with_missing_field(self) -> None:
        """異常系: 必須フィールドが欠けている場合"""
        with pytest.raises(ValidationError):
            MovieMetadata(  # type: ignore
                title="Test Movie",
                japanese_titles=["テスト映画"],
                original_work="原作作品",
                original_authors=["原作者A"],
                release_date="2024-01-01",
                country="Japan",
                distributor="配給会社A",
                production_companies=["制作会社A"],
                box_office="$100M",
                cast=["俳優A"],
                screenwriters=["脚本家A"],
                music=["作曲家B"],
                # voice_actorsが欠けている
            )


class TestMetadataFieldScore:
    """MetadataFieldScoreモデルのテスト"""

    def test_valid_field_score(self) -> None:
        """正常系: スコアが0.0〜5.0の範囲内"""
        score = MetadataFieldScore(
            field_name="title", score=3.5, reasoning="良好なタイトル"
        )
        assert score.field_name == "title"
        assert score.score == 3.5
        assert score.reasoning == "良好なタイトル"

    def test_field_score_boundary_min(self) -> None:
        """正常系: 最小値0.0"""
        score = MetadataFieldScore(field_name="title", score=0.0, reasoning="最悪")
        assert score.score == 0.0

    def test_field_score_boundary_max(self) -> None:
        """正常系: 最大値5.0"""
        score = MetadataFieldScore(field_name="title", score=5.0, reasoning="最高")
        assert score.score == 5.0

    def test_field_score_below_min(self) -> None:
        """異常系: スコアが0.0未満"""
        with pytest.raises(ValidationError):
            MetadataFieldScore(field_name="title", score=-0.1, reasoning="不正")

    def test_field_score_above_max(self) -> None:
        """異常系: スコアが5.0超"""
        with pytest.raises(ValidationError):
            MetadataFieldScore(field_name="title", score=5.1, reasoning="不正")


class TestMetadataEvaluationResult:
    """MetadataEvaluationResultモデルのテスト"""

    def test_valid_evaluation_result(self) -> None:
        """正常系: 有効な評価結果を作成"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良い"),
            MetadataFieldScore(field_name="cast", score=3.5, reasoning="問題なし"),
        ]
        result = MetadataEvaluationResult(
            iteration=1,
            field_scores=field_scores,
            overall_status="pass",
            improvement_suggestions="なし",
        )
        assert result.iteration == 1
        assert len(result.field_scores) == 2
        assert result.overall_status == "pass"

    def test_evaluation_result_with_fail_status(self) -> None:
        """正常系: overall_status='fail'のケース"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=2.0, reasoning="改善が必要")
        ]
        result = MetadataEvaluationResult(
            iteration=1,
            field_scores=field_scores,
            overall_status="fail",
            improvement_suggestions="タイトルを詳細に記載",
        )
        assert result.overall_status == "fail"
        assert result.improvement_suggestions == "タイトルを詳細に記載"


class TestRefinementHistoryEntry:
    """RefinementHistoryEntryモデルのテスト"""

    def test_valid_refinement_history_entry(
        self, sample_movie_metadata: MovieMetadata
    ) -> None:
        """正常系: 有効な改善履歴エントリを作成"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良い")
        ]
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=field_scores,
            overall_status="pass",
            improvement_suggestions="なし",
        )
        entry = RefinementHistoryEntry(
            iteration=1, metadata=sample_movie_metadata, evaluation=evaluation
        )
        assert entry.iteration == 1
        assert entry.metadata == sample_movie_metadata
        assert entry.evaluation == evaluation


class TestMetadataRefinementResult:
    """MetadataRefinementResultモデルのテスト"""

    def test_valid_refinement_result(
        self, sample_movie_metadata: MovieMetadata
    ) -> None:
        """正常系: 有効な改善結果を作成"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良い")
        ]
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=field_scores,
            overall_status="pass",
            improvement_suggestions="なし",
        )
        entry = RefinementHistoryEntry(
            iteration=1, metadata=sample_movie_metadata, evaluation=evaluation
        )
        result = MetadataRefinementResult(
            final_metadata=sample_movie_metadata,
            history=[entry],
            success=True,
            total_iterations=1,
        )
        assert result.final_metadata == sample_movie_metadata
        assert len(result.history) == 1
        assert result.success is True
        assert result.total_iterations == 1

    def test_refinement_result_with_failure(
        self, sample_movie_metadata: MovieMetadata
    ) -> None:
        """正常系: 改善に失敗したケース"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=2.0, reasoning="改善が必要")
        ]
        evaluation = MetadataEvaluationResult(
            iteration=3,
            field_scores=field_scores,
            overall_status="fail",
            improvement_suggestions="タイトルを詳細に記載",
        )
        entry = RefinementHistoryEntry(
            iteration=3, metadata=sample_movie_metadata, evaluation=evaluation
        )
        result = MetadataRefinementResult(
            final_metadata=sample_movie_metadata,
            history=[entry],
            success=False,
            total_iterations=3,
        )
        assert result.success is False
        assert result.total_iterations == 3


class TestBatchRefinementResult:
    """BatchRefinementResultモデルのテスト"""

    def test_valid_batch_refinement_result(
        self, sample_movie_metadata: MovieMetadata
    ) -> None:
        """正常系: 有効なバッチ改善結果を作成"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良い")
        ]
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=field_scores,
            overall_status="pass",
            improvement_suggestions="なし",
        )
        entry = RefinementHistoryEntry(
            iteration=1, metadata=sample_movie_metadata, evaluation=evaluation
        )
        refinement_result = MetadataRefinementResult(
            final_metadata=sample_movie_metadata,
            history=[entry],
            success=True,
            total_iterations=1,
        )

        batch = BatchRefinementResult(
            results=[refinement_result],
            total_count=1,
            success_count=1,
            error_count=0,
            errors=[],
            processing_time=1.23,
        )

        assert batch.total_count == 1
        assert batch.success_count == 1
        assert batch.error_count == 0
        assert batch.processing_time == 1.23
        assert batch.results[0].final_metadata.title == sample_movie_metadata.title

    def test_batch_refinement_result_with_errors(self) -> None:
        """正常系: エラー情報を含むバッチ改善結果"""
        batch = BatchRefinementResult(
            results=[],
            total_count=2,
            success_count=1,
            error_count=1,
            errors=[{"title": "Missing Movie", "message": "Not found"}],
            processing_time=0.5,
        )

        assert batch.error_count == 1
        assert batch.errors == [{"title": "Missing Movie", "message": "Not found"}]


class TestMetadataEvaluationOutput:
    """MetadataEvaluationOutputモデルのテスト"""

    def test_valid_evaluation_output(self) -> None:
        """正常系: 有効な評価出力を作成"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=4.0, reasoning="良い")
        ]
        output = MetadataEvaluationOutput(
            field_scores=field_scores, improvement_suggestions="なし"
        )
        assert len(output.field_scores) == 1
        assert output.improvement_suggestions == "なし"

    def test_evaluation_output_with_suggestions(self) -> None:
        """正常系: 改善提案がある場合"""
        field_scores = [
            MetadataFieldScore(field_name="title", score=2.0, reasoning="改善が必要")
        ]
        output = MetadataEvaluationOutput(
            field_scores=field_scores, improvement_suggestions="タイトルを詳細に記載"
        )
        assert output.improvement_suggestions == "タイトルを詳細に記載"
