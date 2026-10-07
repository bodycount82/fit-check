"""Shared data types.

`SkinProfile` and `Candidate` live here, not in `decision.py`, because both the
advisor and the decision layer need them. Keeping them in a neutral module
avoids a circular import between the two and makes the dependency direction
obvious: advisor and decision both depend on types; neither depends on the other.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cost_model


@dataclass
class SkinProfile:
    """A person's skin readings, 0-100 per concern."""

    concerns: dict[str, float] = field(default_factory=dict)

    def elevated_concerns(self, threshold: float) -> list[str]:
        """Concern names at or above `threshold`."""
        return [k for k, v in self.concerns.items() if v >= threshold]

    @classmethod
    def from_youcam_result(cls, raw: object) -> "SkinProfile":
        """Parse the YouCam skin-analysis payload into a flat concern map.

        YouCam returns a nested structure; we flatten it to name -> score.
        Unknown shapes are tolerated: we take any dict of numbers we find, so
        a schema change on their side degrades instead of crashing.
        """
        concerns: dict[str, float] = {}

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        concerns.setdefault(str(key), float(value))
                    else:
                        walk(value)
            elif isinstance(node, list):
                for index, item in enumerate(node):
                    if isinstance(item, (int, float)) and not isinstance(item, bool):
                        concerns.setdefault(str(index), float(item))
                    else:
                        walk(item)

        walk(raw)
        return cls(concerns=concerns)


@dataclass
class Candidate:
    """One item the user might render.

    Attributes are deliberately limited to what the advisor can actually reason
    about — tone, finish, pattern. An attribute the advisor cannot use would be
    decoration, and the refusal has to be defensible.
    """

    id: str
    name: str
    tone: str = ""
    finish: str = ""
    pattern: str = ""
    render_cost: int = cost_model.COST_CLOTHES_VTO
    render_kind: str = "cloth"  # "cloth" | "ring"
