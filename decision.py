"""The decision layer — the part the YouCam API does not do.

Everything YouCam sells is *generative*: it renders what you ask for. The gap
is that nobody upstream of the render is qualified to ask. People try on the
wrong things, and returns are driven by "it looked different on me".

So this module decides, spends a visible budget on purpose, and — crucially —
says no. A refusal is the one output an image generator cannot produce.
"""

from __future__ import annotations

from dataclasses import dataclass

from advisor import Advisor, Judgement
from cost_model import BudgetLedger, skin_analysis_cost
from models import Candidate, SkinProfile

__all__ = ["Candidate", "SkinProfile", "Decision", "Plan", "plan_fit_check"]


@dataclass
class Decision:
    """The outcome for one candidate: kept or refused, with the reason."""

    candidate: Candidate
    keep: bool
    reason: str
    confidence: float


@dataclass
class Plan:
    """The full plan: what we bought, what we kept, what we refused, and why."""

    skin_cost: int
    decisions: list[Decision]
    kept: list[Candidate]
    refused: list[Decision]
    ledger: BudgetLedger

    @property
    def render_cost(self) -> int:
        return sum(c.render_cost for c in self.kept)

    def summary(self) -> str:
        lines = [
            f"Skin analysis: {self.skin_cost} units (everything else depends on it)",
            f"Candidates considered: {len(self.decisions)}",
            f"Kept: {len(self.kept)}  |  Refused: {len(self.refused)}",
            f"Render budget for kept items: {self.render_cost} units",
        ]
        if self.refused:
            lines.append("")
            lines.append("Refused, with reasons:")
            for d in self.refused:
                lines.append(f"  ✗ {d.candidate.name} — {d.reason}")
        lines.append("")
        lines.append(self.ledger.explain())
        return "\n".join(lines)


def plan_fit_check(
    profile: SkinProfile,
    candidates: list[Candidate],
    advisor: Advisor,
    n_concerns: int = 16,
    hd: bool = True,
    total_units: int = 2040,
) -> Plan:
    """Decide what is worth rendering, refuse the rest, and track the budget.

    Order matters and is deliberate:
      1. Buy the skin read first — everything downstream depends on it, and it
         is the only thing that makes a refusal defensible rather than a guess.
      2. Ask the advisor about every candidate BEFORE spending on renders.
      3. Spend on renders only for what survived.
    """
    ledger = BudgetLedger(total=total_units)

    skin_cost = skin_analysis_cost(n_concerns, hd=hd)
    if not ledger.spend(
        "skin analysis",
        skin_cost,
        "everything downstream depends on this reading, so it is bought first",
    ):
        raise ValueError("Budget too small to afford even the skin analysis.")

    decisions: list[Decision] = []
    kept: list[Candidate] = []
    refused: list[Decision] = []

    for candidate in candidates:
        judgement: Judgement = advisor.judge(profile, candidate)
        decision = Decision(
            candidate=candidate,
            keep=judgement.keep,
            reason=judgement.reason,
            confidence=judgement.confidence,
        )
        decisions.append(decision)
        if judgement.keep:
            kept.append(candidate)
        else:
            refused.append(decision)

    # Spend on the renders we actually chose — and be honest if we can't.
    for candidate in list(kept):
        if ledger.spend(
            f"render: {candidate.name}",
            candidate.render_cost,
            "survived review; the render is the thing the user came for",
        ):
            continue
        # Unaffordable: refuse it explicitly rather than silently dropping it.
        kept.remove(candidate)
        refused.append(
            Decision(
                candidate=candidate,
                keep=False,
                reason=(
                    f"Not rendered: {candidate.render_cost} units needed, "
                    f"{ledger.remaining} left after higher-priority spends."
                ),
                confidence=1.0,
            )
        )

    return Plan(
        skin_cost=skin_cost,
        decisions=decisions,
        kept=kept,
        refused=refused,
        ledger=ledger,
    )
