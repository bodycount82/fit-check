"""Demo data — the catalogue and a plausible skin profile.

Kept separate from `app.py` so the headless demo (`demo.py`) has no Streamlit
dependency. A judge running `python demo.py` should not need a UI framework
installed to see the decision layer work.
"""

from __future__ import annotations

from models import Candidate, SkinProfile

# A small catalogue with attributes the advisor can actually reason about.
# Deliberately chosen to exercise every rule: warm/cool tones, matte/satin/
# metallic finishes, solid/busy patterns.
DEMO_CATALOGUE: list[Candidate] = [
    Candidate("c1", "Rust wool blazer", tone="rust", finish="matte",
              pattern="solid", render_cost=2, render_kind="cloth"),
    Candidate("c2", "Slate grey shirt", tone="cool", finish="matte",
              pattern="solid", render_cost=2, render_kind="cloth"),
    Candidate("c3", "Satin emerald blouse", tone="cool", finish="satin",
              pattern="solid", render_cost=2, render_kind="cloth"),
    Candidate("c4", "Bold floral dress", tone="warm", finish="matte",
              pattern="floral", render_cost=2, render_kind="cloth"),
    Candidate("c5", "Metallic silver top", tone="cool", finish="metallic",
              pattern="solid", render_cost=2, render_kind="cloth"),
    Candidate("c6", "Navy structured jacket", tone="cool", finish="matte",
              pattern="solid", render_cost=2, render_kind="cloth"),
]

# A plausible demo profile: warm undertone with elevated redness and texture.
# This is the shape YouCam's skin analysis returns, flattened to 0-100.
DEMO_PROFILE = SkinProfile(concerns={
    "redness": 68.0,
    "texture": 61.0,
    "pore": 44.0,
    "wrinkle": 38.0,
    "oiliness": 52.0,
    "moisture": 47.0,
    "age_spot": 33.0,
    "dark_circle": 41.0,
})
