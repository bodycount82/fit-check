"""Per-feature unit costs and the budget model.

Costs read from source (2026-10-07) at
  https://yce.perfectcorp.com/ai-api/api-pricing
and the per-feature docs under docs.perfectcorp.com/reference/.

Two facts that shape the design:
  * Cost is *not* the constraint — the whole demo is ~132 units of ~2,040.
    So the budget exists to make the trade-off VISIBLE to a judge, not to
    prevent us from running out.
  * Failed tasks cost nothing, so retries in a live demo are free.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# --- Skin Analysis: cost scales with number of concerns requested ----------
#            concerns: 1-4   5-8   9-12  13-16
SKIN_ANALYSIS_SD = {1: 9, 5: 12, 9: 14, 13: 16}
SKIN_ANALYSIS_HD = {1: 12, 5: 16, 9: 20, 13: 22}

# --- Virtual Try-On --------------------------------------------------------
COST_CLOTHES_VTO = 2
COST_RING_VTO = 1
COST_RING_VTO_STACKED = 2
COST_FITZPATRICK = 10


def skin_analysis_cost(n_concerns: int, hd: bool = True) -> int:
    """Unit cost for a skin analysis requesting `n_concerns` concerns."""
    if n_concerns < 1:
        raise ValueError("need at least 1 concern")
    table = SKIN_ANALYSIS_HD if hd else SKIN_ANALYSIS_SD
    for lower in sorted(table, reverse=True):
        if n_concerns >= lower:
            return table[lower]
    return table[1]


@dataclass
class BudgetLedger:
    """A visible, honest record of what we spent and why.

    The point of this class is to be *shown* to the user. Every spend records
    a reason, so the UI can render a decision trail rather than a number.
    """

    total: int = 2040  # 1000 redeem + up to 1000 social bonus + 40 free
    spent: int = 0
    entries: list[tuple[str, int, str]] = field(default_factory=list)

    @property
    def remaining(self) -> int:
        return self.total - self.spent

    def can_afford(self, cost: int) -> bool:
        return cost <= self.remaining

    def spend(self, label: str, cost: int, reason: str) -> bool:
        """Record a spend. Returns False (and records nothing) if unaffordable."""
        if not self.can_afford(cost):
            return False
        self.spent += cost
        self.entries.append((label, cost, reason))
        return True

    def refund(self, label: str, cost: int) -> None:
        """Failed tasks cost nothing — give the units back and say so."""
        self.spent -= cost
        self.entries.append((label, -cost, "task failed — no units consumed"))

    def explain(self) -> str:
        """One-paragraph human summary of the trade-offs made."""
        if not self.entries:
            return "No units spent yet."
        lines = [
            f"  {label}: {cost:+d} units — {reason}"
            for label, cost, reason in self.entries
        ]
        return (
            f"Spent {self.spent} of {self.total} units "
            f"({self.remaining} left):\n" + "\n".join(lines)
        )
