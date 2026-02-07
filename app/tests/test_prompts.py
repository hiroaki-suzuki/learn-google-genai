"""prompts.pyのテスト"""

import pytest

from movie_metadata.models import (
    MetadataEvaluationResult,
    MetadataFieldScore,
    MovieInput,
    MovieMetadata,
)
from movie_metadata.prompts import (
    build_improvement_proposal_prompt,
    build_metadata_evaluation_prompt,
    build_metadata_fetch_prompt,
)


class TestBuildMetadataEvaluationPrompt:
    """build_metadata_evaluation_prompt関数のテスト"""

    def test_build_prompt_with_normal_data(self):
        """正常なデータでプロンプトが構築されることを確認"""
        title = "Test Movie"
        release_date = "2024-01-01"
        country = "Japan"
        japanese_titles = ["テスト映画", "テストムービー"]
        distributor = "テスト配給"
        box_office = "$1,000,000"
        cast = ["俳優A", "俳優B"]
        music = ["作曲家C"]
        voice_actors = ["声優D"]

        prompt = build_metadata_evaluation_prompt(
            title=title,
            release_date=release_date,
            country=country,
            japanese_titles=japanese_titles,
            distributor=distributor,
            box_office=box_office,
            cast=cast,
            music=music,
            voice_actors=voice_actors,
        )

        # プロンプトに映画情報が含まれていることを確認
        assert "Test Movie" in prompt
        assert "2024-01-01" in prompt
        assert "Japan" in prompt
        assert "テスト映画" in prompt
        assert "テストムービー" in prompt
        assert "テスト配給" in prompt
        assert "$1,000,000" in prompt
        assert "俳優A" in prompt
        assert "作曲家C" in prompt
        assert "声優D" in prompt

        # プロンプトに評価基準の説明が含まれていることを確認
        assert "評価基準" in prompt
        assert "0.0〜5.0" in prompt
        assert "3.5以上" in prompt

    def test_build_prompt_with_empty_lists(self):
        """空のリストでプロンプトが構築されることを確認"""
        title = "Empty Movie"
        release_date = "2024-01-01"
        country = "Japan"
        japanese_titles = []
        distributor = "配給なし"
        box_office = "情報なし"
        cast = []
        music = []
        voice_actors = []

        prompt = build_metadata_evaluation_prompt(
            title=title,
            release_date=release_date,
            country=country,
            japanese_titles=japanese_titles,
            distributor=distributor,
            box_office=box_office,
            cast=cast,
            music=music,
            voice_actors=voice_actors,
        )

        # プロンプトに「情報なし」が含まれることを確認
        assert "情報なし" in prompt
        assert "Empty Movie" in prompt

    def test_build_prompt_with_info_nashi(self):
        """「情報なし」を含むリストでプロンプトが構築されることを確認"""
        title = "No Info Movie"
        release_date = "2024-01-01"
        country = "Japan"
        japanese_titles = ["情報なし"]
        distributor = "情報なし"
        box_office = "情報なし"
        cast = ["情報なし"]
        music = ["情報なし"]
        voice_actors = ["情報なし"]

        prompt = build_metadata_evaluation_prompt(
            title=title,
            release_date=release_date,
            country=country,
            japanese_titles=japanese_titles,
            distributor=distributor,
            box_office=box_office,
            cast=cast,
            music=music,
            voice_actors=voice_actors,
        )

        # プロンプトに「情報なし」が含まれることを確認
        assert "情報なし" in prompt
        assert "No Info Movie" in prompt


class TestBuildImprovementProposalPrompt:
    """build_improvement_proposal_prompt関数のテスト"""

    def test_build_prompt_with_fail_status(self):
        """overall_status='fail'の評価結果でプロンプトが構築されることを確認"""
        movie_input = MovieInput(title="Test Movie", release_date="2024-01-01", country="Japan")
        current_metadata = MovieMetadata(
            title="Test Movie",
            japanese_titles=["テスト映画"],
            release_date="2024-01-01",
            country="Japan",
            distributor="テスト配給",
            box_office="情報なし",
            cast=["俳優A"],
            music=["作曲家B"],
            voice_actors=["声優C"],
        )
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=[
                MetadataFieldScore(
                    field_name="japanese_titles",
                    score=4.0,
                    reasoning="十分な情報が含まれている",
                ),
                MetadataFieldScore(
                    field_name="box_office",
                    score=2.0,
                    reasoning="具体的な金額が不足している",
                ),
            ],
            overall_status="fail",
            improvement_suggestions="box_officeを改善してください",
        )

        prompt = build_improvement_proposal_prompt(
            movie_input=movie_input,
            current_metadata=current_metadata,
            evaluation=evaluation,
        )

        # プロンプトに映画情報が含まれていることを確認
        assert "Test Movie" in prompt
        assert "2024-01-01" in prompt
        assert "Japan" in prompt

        # プロンプトに評価結果が含まれていることを確認
        assert "japanese_titles" in prompt
        assert "4.0" in prompt
        assert "✓ 合格" in prompt
        assert "box_office" in prompt
        assert "2.0" in prompt
        assert "✗ 要改善" in prompt

        # プロンプトに改善提案の説明が含まれていることを確認
        assert "改善提案" in prompt

    def test_build_prompt_with_pass_status(self):
        """overall_status='pass'の評価結果でプロンプトが構築されることを確認"""
        movie_input = MovieInput(title="Pass Movie", release_date="2024-01-01", country="Japan")
        current_metadata = MovieMetadata(
            title="Pass Movie",
            japanese_titles=["パス映画"],
            release_date="2024-01-01",
            country="Japan",
            distributor="パス配給",
            box_office="$1,000,000",
            cast=["俳優A"],
            music=["作曲家B"],
            voice_actors=["声優C"],
        )
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=[
                MetadataFieldScore(
                    field_name="japanese_titles",
                    score=4.5,
                    reasoning="完全な情報が含まれている",
                ),
                MetadataFieldScore(
                    field_name="box_office",
                    score=5.0,
                    reasoning="詳細な金額が記載されている",
                ),
            ],
            overall_status="pass",
            improvement_suggestions="なし",
        )

        prompt = build_improvement_proposal_prompt(
            movie_input=movie_input,
            current_metadata=current_metadata,
            evaluation=evaluation,
        )

        # プロンプトに映画情報が含まれていることを確認
        assert "Pass Movie" in prompt

        # プロンプトに評価結果が含まれていることを確認（すべて合格）
        assert "4.5" in prompt
        assert "5.0" in prompt
        assert "✓ 合格" in prompt

    def test_build_prompt_with_empty_metadata(self):
        """空のメタデータでプロンプトが構築されることを確認"""
        movie_input = MovieInput(title="Empty Movie", release_date="2024-01-01", country="Japan")
        current_metadata = MovieMetadata(
            title="Empty Movie",
            japanese_titles=[],
            release_date="2024-01-01",
            country="Japan",
            distributor="情報なし",
            box_office="情報なし",
            cast=["情報なし"],
            music=[],
            voice_actors=[],
        )
        evaluation = MetadataEvaluationResult(
            iteration=1,
            field_scores=[
                MetadataFieldScore(
                    field_name="japanese_titles",
                    score=1.0,
                    reasoning="情報が不足している",
                ),
            ],
            overall_status="fail",
            improvement_suggestions="すべてのフィールドを改善してください",
        )

        prompt = build_improvement_proposal_prompt(
            movie_input=movie_input,
            current_metadata=current_metadata,
            evaluation=evaluation,
        )

        # プロンプトに映画情報が含まれていることを確認
        assert "Empty Movie" in prompt

        # プロンプトに「情報なし」が含まれることを確認
        assert "情報なし" in prompt


class TestBuildMetadataFetchPrompt:
    """build_metadata_fetch_prompt関数のテスト"""

    def test_build_prompt_without_improvement(self):
        """改善指示なしでプロンプトが構築されることを確認"""
        input_info = "タイトル: Test Movie\n公開日: 2024-01-01\n制作国: Japan"

        prompt = build_metadata_fetch_prompt(input_info=input_info)

        # プロンプトに映画情報が含まれていることを確認
        assert "Test Movie" in prompt
        assert "2024-01-01" in prompt
        assert "Japan" in prompt

        # プロンプトに基本的な指針が含まれていることを確認
        assert "日本語の情報を優先的に使用" in prompt
        assert "情報収集の指針" in prompt

        # 改善指示セクションが含まれていないことを確認
        assert "改善指示" not in prompt

    def test_build_prompt_with_improvement(self):
        """改善指示ありでプロンプトが構築されることを確認"""
        input_info = "タイトル: Test Movie\n公開日: 2024-01-01\n制作国: Japan"
        improvement_instruction = "box_officeに具体的な金額を追加してください"

        prompt = build_metadata_fetch_prompt(
            input_info=input_info,
            improvement_instruction=improvement_instruction,
        )

        # プロンプトに映画情報が含まれていることを確認
        assert "Test Movie" in prompt
        assert "2024-01-01" in prompt
        assert "Japan" in prompt

        # プロンプトに基本的な指針が含まれていることを確認
        assert "日本語の情報を優先的に使用" in prompt

        # 改善指示セクションが含まれていることを確認
        assert "改善指示" in prompt
        assert "box_officeに具体的な金額を追加してください" in prompt

    def test_build_prompt_with_none_improvement(self):
        """improvement_instruction=Noneでプロンプトが構築されることを確認"""
        input_info = "タイトル: None Movie\n公開日: 2024-01-01\n制作国: Japan"

        prompt = build_metadata_fetch_prompt(
            input_info=input_info,
            improvement_instruction=None,
        )

        # プロンプトに映画情報が含まれていることを確認
        assert "None Movie" in prompt

        # 改善指示セクションが含まれていないことを確認
        assert "改善指示" not in prompt

    def test_build_prompt_with_empty_string_improvement(self):
        """improvement_instruction=""（空文字列）でプロンプトが構築されることを確認"""
        input_info = "タイトル: Empty Movie\n公開日: 2024-01-01\n制作国: Japan"

        # 空文字列はFalsyなので、改善指示セクションは追加されない
        prompt = build_metadata_fetch_prompt(
            input_info=input_info,
            improvement_instruction="",
        )

        # プロンプトに映画情報が含まれていることを確認
        assert "Empty Movie" in prompt

        # 改善指示セクションが含まれていないことを確認（空文字列はFalsy）
        assert "改善指示" not in prompt
