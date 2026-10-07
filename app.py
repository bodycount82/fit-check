"""Fit Check — the product surface.

What makes this a product rather than a demo: the screen shows a DECISION.
The chosen render is one column. The refused candidates are the other, each
with the reason it lost. The budget meter shows what was spent and why.

Run:  streamlit run app.py
"""

from __future__ import annotations

import os

import streamlit as st

import cost_model
from advisor import build_advisor
from decision import SkinProfile, plan_fit_check
from demo_data import DEMO_CATALOGUE, DEMO_PROFILE
from youcam_client import YouCamClient, YouCamError, client_from_env

st.set_page_config(page_title="Fit Check", page_icon="🧥", layout="wide")


def render_budget_meter(ledger: cost_model.BudgetLedger) -> None:
    st.subheader("Unit budget")
    used_fraction = ledger.spent / ledger.total if ledger.total else 0
    st.progress(min(used_fraction, 1.0),
                text=f"{ledger.spent} of {ledger.total} units spent "
                     f"({ledger.remaining} left)")
    with st.expander("Why each unit was spent"):
        for label, cost, reason in ledger.entries:
            st.markdown(f"**{label}** — `{cost:+d}` units  \n_{reason}_")


def main() -> None:
    st.title("Fit Check")
    st.caption(
        "An advisor that decides what is worth rendering — and refuses the rest."
    )

    with st.sidebar:
        st.header("Input")
        uploaded = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
        st.caption("No photo? The demo profile below is used.")
        use_demo = st.checkbox("Use demo skin profile", value=True)
        st.divider()
        st.header("Configuration")
        st.text(f"Advisor: {build_advisor().name}")
        st.text(f"API key: {'set' if os.environ.get('YOUCAM_API_KEY') else 'not set'}")

    profile = DEMO_PROFILE
    skin_source = "demo profile"

    if uploaded is not None and not use_demo:
        if not os.environ.get("YOUCAM_API_KEY"):
            st.warning(
                "A photo was provided but no YOUCAM_API_KEY is set. "
                "Falling back to the demo profile."
            )
        else:
            try:
                with st.spinner("Running YouCam skin analysis…"):
                    client = client_from_env()
                    tmp_path = os.path.join("/tmp", "fitcheck_upload.jpg")
                    with open(tmp_path, "wb") as fh:
                        fh.write(uploaded.getbuffer())
                    file_id = client.upload_file(tmp_path)
                    result = client.skin_analysis(file_id)
                    if result.ok:
                        profile = SkinProfile.from_youcam_result(result.raw)
                        skin_source = "YouCam skin analysis (live)"
                    else:
                        st.error("Skin analysis failed; using the demo profile.")
            except YouCamError as exc:
                st.error(f"YouCam error: {exc}. Using the demo profile.")

    st.info(f"Skin readings from: **{skin_source}**")

    advisor = build_advisor()
    plan = plan_fit_check(profile, DEMO_CATALOGUE, advisor, n_concerns=16, hd=True)

    col_kept, col_refused = st.columns(2)

    with col_kept:
        st.subheader(f"Chosen — worth rendering ({len(plan.kept)})")
        if not plan.kept:
            st.write("Nothing survived review.")
        for candidate in plan.kept:
            with st.container(border=True):
                st.markdown(f"**{candidate.name}**")
                st.caption(
                    f"{candidate.tone} · {candidate.finish} · {candidate.pattern} "
                    f"— {candidate.render_cost} units"
                )
                decision = next(
                    d for d in plan.decisions if d.candidate.id == candidate.id
                )
                st.write(decision.reason)

    with col_refused:
        st.subheader(f"Refused — with reasons ({len(plan.refused)})")
        if not plan.refused:
            st.write("Nothing was refused.")
        for decision in plan.refused:
            with st.container(border=True):
                st.markdown(f"**✗ {decision.candidate.name}**")
                st.caption(
                    f"{decision.candidate.tone} · {decision.candidate.finish} · "
                    f"{decision.candidate.pattern}"
                )
                st.write(decision.reason)

    st.divider()
    render_budget_meter(plan.ledger)

    with st.expander("Full decision trail (what the API does not give you)"):
        st.code(plan.summary(), language="text")


if __name__ == "__main__":
    main()
