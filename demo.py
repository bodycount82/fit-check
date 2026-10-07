"""Fit Check — headless demo.

Runs the whole decision pipeline without the UI, so it can be shown in a
terminal, recorded for the demo video, or run in CI. No API key required:
the rule-based advisor and the demo profile are self-contained.

    python demo.py
"""

from __future__ import annotations

from advisor import build_advisor
from decision import SkinProfile, plan_fit_check
from demo_data import DEMO_CATALOGUE, DEMO_PROFILE


def main() -> int:
    advisor = build_advisor()
    profile: SkinProfile = DEMO_PROFILE

    plan = plan_fit_check(
        profile, DEMO_CATALOGUE, advisor, n_concerns=16, hd=True
    )

    print("=" * 72)
    print("FIT CHECK — a decision, not a render")
    print("=" * 72)
    print(f"Advisor: {advisor.name}")
    print()
    print("Skin readings (0-100, above 55 is elevated):")
    for name, value in sorted(profile.concerns.items(), key=lambda kv: -kv[1]):
        flag = "  <-- elevated" if value >= 55 else ""
        print(f"  {name:<14} {value:5.0f}{flag}")
    print()
    print("-" * 72)
    print(f"CHOSEN ({len(plan.kept)}):")
    for candidate in plan.kept:
        print(f"  + {candidate.name}")
    print()
    print(f"REFUSED ({len(plan.refused)}):")
    for decision in plan.refused:
        print(f"  x {decision.candidate.name}")
        print(f"      {decision.reason}")
    print()
    print("-" * 72)
    print(plan.ledger.explain())
    print()
    print("=" * 72)
    print("One HD skin read (22 units) bought every decision below it.")
    print(f"Total spent: {plan.ledger.spent} of {plan.ledger.total} units.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
