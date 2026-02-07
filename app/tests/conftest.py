"""pytest共通フィクスチャ"""

from unittest.mock import MagicMock

import pytest

from movie_metadata.genai_client import GenAIClient
from movie_metadata.models import MovieInput, MovieMetadata


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
        original_work="オリジナル",
        original_authors=[],
        release_date="2024-01-01",
        country="Japan",
        distributor="テスト配給",
        production_companies=["テスト制作"],
        box_office="$1M",
        cast=["俳優A"],
        screenwriters=["脚本家D"],
        music=["作曲家B"],
        voice_actors=["声優C"],
    )


@pytest.fixture
def sample_metadata_json(sample_movie_metadata: MovieMetadata) -> str:
    """テスト用MovieMetadataのJSON文字列"""
    return sample_movie_metadata.model_dump_json()


@pytest.fixture
def mock_genai_client() -> MagicMock:
    """モック化されたGenAIClientフィクスチャ"""
    return MagicMock(spec=GenAIClient)
