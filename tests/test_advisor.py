"""Tests for advisor.py — the rule-based advisor's judgements."""

from __future__ import annotations

import pytest

from advisor import RuleAdvisor, Judgement
from decision import Candidate, SkinProfile


class TestRuleAdvisor:
    """The published reference advisor refuses with stated reasons."""

    def setup_method(self):
        self.advisor = RuleAdvisor()
        self.profile = SkinProfile(concerns={
            "redness": 70.0,
            "texture": 60.0,
            "pore": 40.0,
            "wrinkle": 30.0,
            "oiliness": 65.0,
            "moisture": 45.0,
            "age_spot": 35.0,
            "dark_circle": 40.0,
        })

    def test_refuses_warm_tone_with_redness(self):
        """Warm tone + elevated redness → refused."""
        candidate = Candidate("c1", "Rust blazer", tone="rust", finish="matte")
        judgement = self.advisor.judge(self.profile, candidate)
        assert judgement.keep is False
        assert "warm" in judgement.reason.lower()
        assert "redness" in judgement.reason.lower()
        assert judgement.confidence > 0.5

    def test_refuses_satin_with_oiliness(self):
        """Satin finish + elevated oiliness → refused."""
        candidate = Candidate("c2", "Satin blouse", tone="cool", finish="satin")
        judgement = self.advisor.judge(self.profile, candidate)
        assert judgement.keep is False
        assert "satin" in judgement.reason.lower() or "shine" in judgement.reason.lower()

    def test_refuses_floral_with_texture(self):
        """Busy pattern + elevated texture → refused."""
        candidate = Candidate("c3", "Floral dress", tone="warm", finish="matte", pattern="floral")
        judgement = self.advisor.judge(self.profile, candidate)
        assert judgement.keep is False
        assert "texture" in judgement.reason.lower() or "pattern" in judgement.reason.lower()

    def test_keeps_neutral_item(self):
        """Cool tone, matte finish, solid pattern → kept when no concern fires."""
        candidate = Candidate("c4", "Navy jacket", tone="cool", finish="matte", pattern="solid")
        judgement = self.advisor.judge(self.profile, candidate)
        assert judgement.keep is True

    def test_keeps_item_when_concerns_are_low(self):
        """If no concerns are elevated, everything is kept."""
        low_profile = SkinProfile(concerns={
            "redness": 20.0, "texture": 15.0, "pore": 10.0,
            "wrinkle": 10.0, "oiliness": 15.0, "moisture": 20.0,
            "age_spot": 10.0, "dark_circle": 15.0,
        })
        candidate = Candidate("c5", "Rust blazer", tone="rust", finish="matte")
        judgement = self.advisor.judge(low_profile, candidate)
        assert judgement.keep is True

    def test_confidence_bounds(self):
        """Confidence should be between 0 and 1."""
        for candidate in [
            Candidate("c1", "Rust blazer", tone="rust", finish="matte"),
            Candidate("c2", "Navy jacket", tone="cool", finish="matte", pattern="solid"),
        ]:
            judgement = self.advisor.judge(self.profile, candidate)
            assert 0 <= judgement.confidence <= 1.0

    def test_name_is_descriptive(self):
        assert self.advisor.name == "rule-based (published reference)"

    def test_refusal_has_reason(self):
        """Every refusal must have a non-empty reason — no silent rejections."""
        candidate = Candidate("c1", "Rust blazer", tone="rust", finish="matte")
        judgement = self.advisor.judge(self.profile, candidate)
        assert not judgement.keep
        assert len(judgement.reason) > 10

    def test_no_empty_reasons(self):
        """Every judgement, kept or refused, must have a stated reason."""
        for candidate in [
            Candidate("c1", "Rust blazer", tone="rust", finish="matte"),
            Candidate("c2", "Navy jacket", tone="cool", finish="matte", pattern="solid"),
        ]:
            judgement = self.advisor.judge(self.profile, candidate)
            assert len(judgement.reason) > 0


class TestRuleAdvisorEdgeCases:
    """Edge cases: unknown attributes, empty profiles, etc."""

    def test_unknown_tone_is_safe(self):
        """An unknown tone doesn't crash the advisor."""
        profile = SkinProfile(concerns={"redness": 70.0})
        candidate = Candidate("c1", "Mystery top", tone="nebula", finish="matte")
        judgement = RuleAdvisor().judge(profile, candidate)
        assert isinstance(judgement, Judgement)

    def test_empty_profile_keeps_everything(self):
        """An empty profile has no elevated concerns → everything kept."""
        profile = SkinProfile(concerns={})
        candidate = Candidate("c1", "Rust blazer", tone="rust", finish="matte")
        judgement = RuleAdvisor().judge(profile, candidate)
        assert judgement.keep is True

    def test_all_elevated_concerns(self):
        """When everything is elevated, more items should be refused."""
        profile = SkinProfile(concerns={
            "redness": 90.0, "texture": 85.0, "pore": 80.0,
            "wrinkle": 75.0, "oiliness": 90.0, "moisture": 30.0,
            "age_spot": 70.0, "dark_circle": 60.0,
        })
        candidates = [
            Candidate("c1", "Rust blazer", tone="rust", finish="matte"),
            Candidate("c2", "Satin blouse", tone="cool", finish="satin"),
            Candidate("c3", "Floral dress", tone="warm", finish="matte", pattern="floral"),
            Candidate("c4", "Metallic top", tone="cool", finish="metallic"),
            Candidate("c5", "Navy jacket", tone="cool", finish="matte", pattern="solid"),
        ]
        kept = sum(1 for c in candidates if RuleAdvisor().judge(profile, c).keep)
        refused = sum(1 for c in candidates if not RuleAdvisor().judge(profile, c).keep)
        # With all concerns high, at least 3 should be refused.
        assert refused >= 3
        assert kept >= 1  # solid/cool/matte should still survive
