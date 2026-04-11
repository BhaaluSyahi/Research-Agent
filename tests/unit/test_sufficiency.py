"""Unit tests for sufficiency.py."""

from uuid import uuid4
import pytest
from app.submodules.matching.schemas import InformalMatch
from app.submodules.matching.sufficiency import is_rag_sufficient


@pytest.fixture
def mock_matches():
    return [
        InformalMatch(
            entry_id=uuid4(),
            title="Match 1",
            summary="Summary 1",
            source_url="https://s1.com",
            trust_score=0.8,
            cosine_score=0.85,
            relevance_reason="Reason 1",
            topic_tags=["floods"],
            geo_tags=["kerala"],
            entities={"people": ["Person A"], "orgs": ["Org X"]}
        ),
        InformalMatch(
            entry_id=uuid4(),
            title="Match 2",
            summary="Summary 2",
            source_url="https://s2.com",
            trust_score=0.7,
            cosine_score=0.80,
            relevance_reason="Reason 2",
            topic_tags=["floods"],
            geo_tags=["kerala"],
            entities={"people": ["Person B"], "orgs": []}
        ),
        InformalMatch(
            entry_id=uuid4(),
            title="Match 3",
            summary="Summary 3",
            source_url="https://s3.com",
            trust_score=0.6,
            cosine_score=0.60,
            relevance_reason="Reason 3",
            topic_tags=["floods"],
            geo_tags=["kerala"],
            entities={"people": [], "orgs": ["Org Y"]}
        )
    ]


def test_sufficiency_met(mock_matches):
    assert is_rag_sufficient(mock_matches) is True


def test_insufficiency_too_few_results(mock_matches):
    # Only 2 matches
    assert is_rag_sufficient(mock_matches[:2]) is False


def test_insufficiency_low_top_score(mock_matches):
    # All scores < 0.75
    for m in mock_matches:
        m.cosine_score = 0.70
    assert is_rag_sufficient(mock_matches) is False


def test_insufficiency_not_enough_distinct_entities(mock_matches):
    # Only 1 distinct entity across all
    for m in mock_matches:
        m.entities = {"people": ["Lone Hero"], "orgs": []}
    assert is_rag_sufficient(mock_matches) is False


def test_sufficiency_empty_list():
    assert is_rag_sufficient([]) is False
