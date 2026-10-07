# Fit Check — Devpost submission copy

## Project name

Fit Check — a refusal-and-budget advisor for virtual try-on

## One-line description

An advisor that decides what is worth rendering — and refuses the rest.

## Problem statement

Everything YouCam sells is *generative*: it renders what you ask for. But nobody upstream of the render is qualified to ask. People try on the wrong things. eCommerce returns are driven by "it looked different on me." The gap in the problem space is that there is no system that reasons about whether a render was a good idea before committing to it.

## Solution

Fit Check is a **refusal-and-budget advisor** that sits between the user and the YouCam API. It reads a person's skin analysis, evaluates a catalogue of candidate items against the skin profile, and decides what is worth rendering — and what is not.

The key output is a **refusal with a stated reason**: "This is a warm, saturated tone and your redness reading is 68/100 — warm tones amplify facial redness." A refusal is the one output an image generator cannot produce, so it can't be confused with the vendor's own getting-started page.

## How it works

1. **Upload** a photo (or use the built-in demo profile) and run a YouCam Skin Analysis (up to 16 concerns, HD or SD).
2. **Evaluate** a catalogue of candidate items against the skin profile using a rule-based advisor that reasons about tone, finish, and pattern.
3. **Refuse** items the analysis argues against — and show the reasoning.
4. **Spend deliberately**: a visible unit budget, per-render cost read from the machine-readable cost API, and a stated trade-off.
5. **Show** the rejected candidates alongside the chosen one, each with the reason it lost.

## YouCam APIs used

- **Skin Analysis (S2S API)** — `POST /s2s/v2.0/task/skin-analysis` with up to 16 concerns, HD or SD. Returns a skin profile with 0-100 scores per concern.
- **Virtual Try-On (S2S API)** — `POST /s2s/v2.0/task/cloth` for clothing renders (~2 units each).
- **Unit cost API** — per-feature costs are machine-readable at `yce.perfectcorp.com/ai-api/api-pricing`, so the budget is real engineering, not glue.

## Architecture

Three layers, deliberately separate:

- **API client** (`youcam_client.py`): thin, honest client over the YouCam S2S API. Auth, upload, task submit, poll, fetch result. Nothing clever on purpose.
- **Decision layer** (`decision.py`): reads the skin profile, asks the advisor about every candidate, spends a visible budget, and produces a plan: what was kept, what was refused, and why.
- **Advisor** (`advisor.py`): the pluggable interface. The published repo ships one honest reference implementation (rule-based, deterministic, offline). An optional private drop-in can implement the same interface with a different brain.

## Judging criteria

### Technological Implementation

The project integrates YouCam Skin Analysis (up to 16 concerns, HD/SD), Virtual Try-On, and the machine-readable cost API. The cost-aware budget is real engineering: every spend records a reason, the ledger tracks refunds for failed tasks, and the UI shows a visible budget meter. The API client is deliberately thin and honest — the interesting engineering is in the decision layer.

### Design

A complete, coherent product experience — not just a technical proof of concept. The screen shows a DECISION: two columns (chosen and refused), each with the reason. The budget meter shows what was spent and why. The decision trail is expandable. The headless demo (`python demo.py`) runs standalone with no API key, no network, no UI framework.

### Potential Impact

Returns in eCommerce are a specific, quantified problem. A system that refuses bad renders before they happen directly addresses the root cause: people trying on things that don't match their skin profile. The refusal mechanism is the one output an image generator cannot produce, so it's a genuinely new product surface.

### Quality of the Idea

The obvious submission — "an agent that calls the YouCam tools" — is now a configuration file. Perfect Corp ships three hosted MCP servers with 99 tools that make this integration trivial. So the integration is given, and the decision layer is the whole product. A refusal is the one output an image generator cannot produce. The repo demonstrates genuine understanding of the problem space: the advisor reads the skin profile and produces genuine refusals with stated reasons, not disclaimers.

## Running the project

```bash
pip install -r requirements.txt
python demo.py          # standalone demo — no API key needed
streamlit run app.py    # interactive UI — API key for live skin analysis
pytest -q               # 70 tests
```

## What is deliberately NOT included

- The private/drop-in advisor implementation.
- Any API keys, tokens or credentials.
- Any third-party source code not covered by this licence.

The repo runs standalone with the rule-based reference advisor.

## Licence

MIT — see LICENSE.
