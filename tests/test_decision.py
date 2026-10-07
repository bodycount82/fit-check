"""Tests for decision.py — the full plan pipeline."""

from __future__ import annotations

import pytest

from advisor import RuleAdvisor
from decision import Candidate, SkinProfile, plan_fit_check


class TestPlanFitCheck:
    """The full decision pipeline: skin read → judge → spend → plan."""

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
        self.candidates = [
            Candidate("c1", "Rust blazer", tone="rust", finish="matte"),
            Candidate("c2", "Satin blouse", tone="cool", finish="satin"),
            Candidate("c3", "Floral dress", tone="warm", finish="matte", pattern="floral"),
            Candidate("c4", "Navy jacket", tone="cool", finish="matte", pattern="solid"),
        ]

    def test_plan_has_skin_cost(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        assert plan.skin_cost == 22  # 16-concern HD

    def test_plan_has_decisions_for_all_candidates(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        assert len(plan.decisions) == 4

    def test_plan_splits_into_kept_and_refused(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        assert len(plan.kept) + len(plan.refused) == 4

    def test_plan_refuses_warm_tone_with_redness(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        refused_names = [d.candidate.name for d in plan.refused]
        assert "Rust blazer" in refused_names

    def test_plan_refuses_satin_with_oiliness(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        refused_names = [d.candidate.name for d in plan.refused]
        assert "Satin blouse" in refused_names

    def test_plan_keeps_neutral_item(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        kept_names = [c.name for c in plan.kept]
        assert "Navy jacket" in kept_names

    def test_plan_tracks_budget(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        # Skin (22) + kept renders (2 each) = 22 + N*2
        expected = 22 + len(plan.kept) * 2
        assert plan.ledger.spent == expected

    def test_plan_summary_is_readable(self):
        plan = plan_fit_check(self.profile, self.candidates, self.advisor)
        summary = plan.summary()
        assert "Skin analysis" in summary
        assert "Refused" in summary
        assert "Rust blazer" in summary
        assert "Satin blouse" in summary

    def test_plan_with_no_elevated_concerns_keeps_all(self):
        """When nothing is elevated, nothing is refused by rules."""
        profile = SkinProfile(concerns={
            "redness": 20.0, "texture": 15.0, "pore": 10.0,
            "wrinkle": 10.0, "oiliness": 15.0, "moisture": 20.0,
            "age_spot": 10.0, "dark_circle": 15.0,
        })
        plan = plan_fit_check(profile, self.candidates, self.advisor)
        assert len(plan.refused) == 0
        assert len(plan.kept) == 4

    def test_plan_spends_what_it_can_afford(self):
        """With 25 units: 22 buys the skin read, 3 left buys exactly one render.

        This is the correct behaviour, not a bug: the budget is spent greedily
        in catalogue order, and whatever cannot be afforded is refused with a
        stated reason rather than silently dropped.
        """
        plan = plan_fit_check(
            self.profile, self.candidates, self.advisor,
            total_units=25
        )
        assert plan.skin_cost == 22
        assert len(plan.kept) == 1  # one 2-unit render fits in the 3 left
        assert plan.ledger.spent == 24
        assert plan.ledger.remaining == 1

    def test_plan_refuses_everything_when_budget_is_fully_spent(self):
        """If only the skin read is affordable, every render is refused.

        The reasons differ by cause, and that is correct: an item the advisor
        rejected is refused on skin grounds, while an item the advisor KEPT but
        the budget could not afford is refused on budget grounds. Both must
        state their reason; they must not be the same reason.
        """
        plan = plan_fit_check(
            self.profile, self.candidates, self.advisor,
            total_units=22  # exactly the skin read, nothing left
        )
        assert plan.skin_cost == 22
        assert len(plan.kept) == 0
        assert len(plan.refused) == 4

        # Every refusal states a reason, and none is empty.
        assert all(d.reason.strip() for d in plan.refused)

        # Exactly one item was advisor-approved but budget-refused.
        budget_refusals = [d for d in plan.refused if "units" in d.reason.lower()]
        assert len(budget_refusals) == 1
        assert budget_refusals[0].candidate.name == "Navy jacket"

        # The other three were refused by the advisor, on skin grounds.
        advisor_refusals = [d for d in plan.refused if d not in budget_refusals]
        assert len(advisor_refusals) == 3
        assert all("units" not in d.reason.lower() for d in advisor_refusals)

    def test_plan_cannot_afford_skin_read(self):
        """A budget below the skin read is a hard error, not a silent no-op."""
        with pytest.raises(ValueError, match="Budget too small"):
            plan_fit_check(
                self.profile, self.candidates, self.advisor, total_units=10
            )

    def test_plan_with_empty_candidates(self):
        """Edge case: no candidates → empty plan."""
        plan = plan_fit_check(self.profile, [], self.advisor)
        assert len(plan.kept) == 0
        assert len(plan.refused) == 0
        assert plan.skin_cost == 22

    def test_plan_with_one_candidate(self):
        """Edge case: single candidate."""
        plan = plan_fit_check(self.profile, [self.candidates[3]], self.advisor)
        assert len(plan.decisions) == 1
        assert plan.skin_cost == 22


class TestSkinProfileFromYoucamResult:
    """Parsing the YouCam skin-analysis payload."""

    def test_flat_dict(self):
        raw = {"redness": 70.0, "texture": 60.0}
        profile = SkinProfile.from_youcam_result(raw)
        assert profile.concerns["redness"] == 70.0
        assert profile.concerns["texture"] == 60.0

    def test_nested_dict(self):
        raw = {
            "result": {
                "concerns": {
                    "redness": 70.0,
                    "pore": 40.0,
                }
            }
        }
        profile = SkinProfile.from_youcam_result(raw)
        assert profile.concerns["redness"] == 70.0
        assert profile.concerns["pore"] == 40.0

    def test_deeply_nested(self):
        raw = {
            "outer": {
                "middle": {
                    "inner": {
                        "redness": 70.0,
                        "texture": 60.0,
                    }
                }
            }
        }
        profile = SkinProfile.from_youcam_result(raw)
        assert profile.concerns["redness"] == 70.0
        assert profile.concerns["texture"] == 60.0

    def test_ignores_non_numbers(self):
        raw = {"redness": 70.0, "task_id": "abc123", "status": "success"}
        profile = SkinProfile.from_youcam_result(raw)
        assert "redness" in profile.concerns
        assert "task_id" not in profile.concerns
        assert "status" not in profile.concerns

    def test_empty_result(self):
        profile = SkinProfile.from_youcam_result({})
        assert profile.concerns == {}

    def test_list_of_numbers(self):
        """If the API returns a list of numbers, we take them all."""
        raw = [10.0, 20.0, 30.0]
        profile = SkinProfile.from_youcam_result(raw)
        # All three numbers are found, keyed by their list index
        assert len(profile.concerns) == 3


class TestSkinProfileElevatedConcerns:
    """Threshold-based elevation detection."""

    def test_threshold_55(self):
        profile = SkinProfile(concerns={"redness": 55.0, "pore": 54.9})
        elevated = profile.elevated_concerns(55.0)
        assert "redness" in elevated
        assert "pore" not in elevated

    def test_all_below_threshold(self):
        profile = SkinProfile(concerns={"redness": 50.0, "pore": 40.0})
        assert profile.elevated_concerns(55.0) == []

    def test_all_above_threshold(self):
        profile = SkinProfile(concerns={"redness": 70.0, "pore": 80.0, "texture": 60.0})
        elevated = profile.elevated_concerns(55.0)
        assert len(elevated) == 3
