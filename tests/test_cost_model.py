"""Tests for cost_model.py — unit costs and the budget ledger."""

from __future__ import annotations

import pytest

import cost_model


class TestSkinAnalysisCost:
    """Unit costs for skin analysis scale with the number of concerns."""

    def test_sd_1_to_4(self):
        for n in range(1, 5):
            assert cost_model.skin_analysis_cost(n, hd=False) == 9

    def test_sd_5_to_8(self):
        for n in range(5, 9):
            assert cost_model.skin_analysis_cost(n, hd=False) == 12

    def test_sd_9_to_12(self):
        for n in range(9, 13):
            assert cost_model.skin_analysis_cost(n, hd=False) == 14

    def test_sd_13_to_16(self):
        for n in range(13, 17):
            assert cost_model.skin_analysis_cost(n, hd=False) == 16

    def test_hd_1_to_4(self):
        for n in range(1, 5):
            assert cost_model.skin_analysis_cost(n, hd=True) == 12

    def test_hd_5_to_8(self):
        for n in range(5, 9):
            assert cost_model.skin_analysis_cost(n, hd=True) == 16

    def test_hd_9_to_12(self):
        for n in range(9, 13):
            assert cost_model.skin_analysis_cost(n, hd=True) == 20

    def test_hd_13_to_16(self):
        for n in range(13, 17):
            assert cost_model.skin_analysis_cost(n, hd=True) == 22

    def test_hd_16_is_22(self):
        """The full demo uses 16-concern HD = 22 units."""
        assert cost_model.skin_analysis_cost(16, hd=True) == 22

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="need at least 1 concern"):
            cost_model.skin_analysis_cost(0)

    def test_hd_is_2x_sd_for_small_concerns(self):
        """HD is always more expensive than SD for the same concern count."""
        for n in range(1, 17):
            assert cost_model.skin_analysis_cost(n, hd=True) >= cost_model.skin_analysis_cost(n, hd=False)


class TestBudgetLedger:
    """The budget ledger tracks spends, refunds, and explains."""

    def test_initial_state(self):
        ledger = cost_model.BudgetLedger(total=2040)
        assert ledger.spent == 0
        assert ledger.remaining == 2040
        assert ledger.entries == []

    def test_spend(self):
        ledger = cost_model.BudgetLedger(total=2040)
        ok = ledger.spend("skin", 22, "first read")
        assert ok is True
        assert ledger.spent == 22
        assert ledger.remaining == 2018
        assert len(ledger.entries) == 1

    def test_spend_refuses_when_unaffordable(self):
        ledger = cost_model.BudgetLedger(total=100)
        ledger.spend("skin", 90, "first read")
        ok = ledger.spend("render", 20, "too much")
        assert ok is False
        assert ledger.spent == 90  # nothing changed

    def test_refund(self):
        ledger = cost_model.BudgetLedger(total=2040)
        ledger.spend("skin", 22, "first read")
        ledger.refund("skin", 22)
        assert ledger.spent == 0
        assert ledger.remaining == 2040
        assert len(ledger.entries) == 2  # spend + refund

    def test_explain_empty(self):
        ledger = cost_model.BudgetLedger(total=2040)
        assert "No units spent yet." in ledger.explain()

    def test_explain_populated(self):
        ledger = cost_model.BudgetLedger(total=2040)
        ledger.spend("skin", 22, "first read")
        ledger.spend("render", 2, "kept item")
        explanation = ledger.explain()
        assert "22" in explanation
        assert "2" in explanation
        assert "first read" in explanation
        assert "kept item" in explanation

    def test_can_afford_boundary(self):
        ledger = cost_model.BudgetLedger(total=100)
        assert ledger.can_afford(100) is True
        assert ledger.can_afford(101) is False

    def test_full_demo_budget(self):
        """The full demo: 22 skin + 6 renders at 2 each = 34 units."""
        ledger = cost_model.BudgetLedger(total=2040)
        assert ledger.spend("skin", 22, "first read")
        for i in range(6):
            assert ledger.spend(f"render {i}", 2, "kept")
        assert ledger.spent == 34
        assert ledger.remaining == 2006
