"""Tests for error chain DTO objects (LinkLogExtra, CrossingLogExtra)."""

import pytest
from dataclasses import FrozenInstanceError

from domain_errors.services.chain.chain_objects import CrossingLogExtra
from domain_errors.services.chain.chain_objects import LinkLogExtra


class TestLinkLogExtra:
    """Tests for LinkLogExtra DTO."""

    def test_construction(self) -> None:
        """LinkLogExtra can be constructed with all fields."""
        extra = LinkLogExtra(
            type="ValueError",
            message="invalid",
            code="VAL_001",
            domain="validation",
            via="root",
            context={"user_id": 123},
        )
        assert extra.type == "ValueError"
        assert extra.message == "invalid"
        assert extra.code == "VAL_001"
        assert extra.domain == "validation"
        assert extra.via == "root"
        assert extra.context == {"user_id": 123}

    def test_frozen(self) -> None:
        """LinkLogExtra is frozen."""
        extra = LinkLogExtra(
            type="ValueError",
            message="test",
            code="X",
            domain="test",
            via="root",
            context={},
        )
        with pytest.raises(FrozenInstanceError):
            extra.type = "TypeError"  # type: ignore


class TestCrossingLogExtra:
    """Tests for CrossingLogExtra DTO."""

    def test_construction(self) -> None:
        """CrossingLogExtra can be constructed with all fields."""
        extra = CrossingLogExtra(
            cause_type="ValueError",
            cause_domain="validation",
            effect_type="RuntimeError",
            effect_domain="application",
        )
        assert extra.cause_type == "ValueError"
        assert extra.cause_domain == "validation"
        assert extra.effect_type == "RuntimeError"
        assert extra.effect_domain == "application"

    def test_frozen(self) -> None:
        """CrossingLogExtra is frozen."""
        extra = CrossingLogExtra(
            cause_type="ValueError",
            cause_domain="validation",
            effect_type="RuntimeError",
            effect_domain="application",
        )
        with pytest.raises(FrozenInstanceError):
            extra.cause_type = "TypeError"  # type: ignore
