# Fit Check

> An advisor that decides what is worth rendering — and refuses the rest.

**Submitted to:** YouCam API Skin AI & E-Commerce Hackathon — https://youcam-api-skin-ai-ecommerce-vto.devpost.com
**Team:** Damir and Genesis

---

## What it is

Fit Check is a **refusal-and-budget advisor** for virtual try-on. Everything YouCam sells is *generative*: it renders what you ask for. The gap is that nobody upstream of the render is qualified to ask. People try on the wrong things; eCommerce returns are driven by "it looked different on me."

Fit Check reads a person's skin analysis, reasons about whether each candidate item is a good match, and **says no** — with a stated reason, not a disclaimer. It spends a visible unit budget on purpose, showing the trade-off between a skin read and the renders it buys.

## What it does

- Upload a photo (or use the built-in demo profile) and run a **YouCam Skin Analysis** (up to 16 concerns, HD or SD).
- Evaluate a catalogue of candidate items against the skin profile using a **rule-based advisor** that reasons about tone, finish, and pattern.
- **Refuse** items the analysis argues against — and show the reasoning. "This is a warm, saturated tone and your redness reading is 68/100 — warm tones amplify facial redness."
- **Spend deliberately**: a visible unit budget, per-render cost read from the machine-readable cost API, and a stated trade-off.
- Show the rejected candidates **alongside** the chosen one, each with the reason it lost. A judge sees a decision, not a picture.

## How to run it (3 steps)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure (copy the example and fill in your own keys)
cp .env.example .env
# Edit .env and add your YouCam API key (get one at:
#   https://yce.perfectcorp.com/api-console/en/api-keys/)

# 3. Run the headless demo (no API key needed)
python demo.py

# Or run the interactive UI (requires API key for live skin analysis)
streamlit run app.py
```

It runs **standalone** — no external service beyond the YouCam API is required. The rule-based advisor and demo profile are self-contained.

## Architecture

```
+-------------+      +------------------+      +---------------------+
|  Entrypoint | ---> |  Decision layer  | ---> |  YouCam API         |
|  (demo.py)  |      |  (published)     |      |  (their side)       |
+-------------+      +------------------+      +---------------------+
                            ^
                            |  same interface
                     +------+-------+
                     | private      |   NOT in this repo.
                     | drop-in      |   Optional. Judges never need it.
                     +--------------+
```

### The decision layer

The decision layer is the heart of the product. It is deliberately separate from the API client:

- `youcam_client.py` — thin, honest client over the YouCam S2S API. Auth, upload, task submit, poll, fetch result. Nothing clever on purpose.
- `decision.py` — reads the skin profile, asks the advisor about every candidate, spends a visible budget, and produces a plan: what was kept, what was refused, and why.
- `advisor.py` — the pluggable interface. The published repo ships one honest reference implementation (rule-based, deterministic, offline). An optional private drop-in can implement the same interface with a different brain. It is **deliberately not included** and is **never committed**.
- `cost_model.py` — per-feature unit costs and a budget ledger that tracks every spend with a reason.

### The pluggable-adapter rule (important)

This repo publishes a **thin adapter** and one honest **reference implementation** so that anyone — including judges — can clone it and run it end to end.

An optional **private drop-in** can implement the same interface with a different brain. It is **deliberately not included** and is **never committed**. Nothing in this repository requires it.

**Why this is safe and legitimate:** the submitted project is the adapter, and the adapter runs standalone. The private implementation is a replacement for the reference one, not a dependency of the public code.

## What is deliberately NOT included

- The private/drop-in advisor implementation (if any).
- Any API keys, tokens or credentials.
- Any third-party source code not covered by this licence.

## Configuration

All configuration is read from the environment. See `.env.example`.

| Variable | Required | Purpose |
|---|---|---|
| `YOUCAM_API_KEY` | no* | Auth for the YouCam S2S API. Not needed for the standalone demo. |
| `YOUCAM_API_BASE` | no | Base host for the server-to-server API. Defaults to `https://yce-api-01.perfectcorp.com`. |
| `FITCHECK_ADVISOR` | no | Private drop-in spec: `module:ClassName`. Empty = rule-based reference. |
| `OPENAI_API_KEY` | no | If using an LLM-backed advisor drop-in. |
| `OPENAI_BASE_URL` | no | Base URL for the LLM endpoint. |

*The standalone demo (`python demo.py`) works with no API key at all.

## Testing

```bash
pytest -q
```

70 tests covering:
- **Cost model** — unit costs for every concern band, budget ledger spends/refunds/explain
- **Advisor** — rule-based judgements for every combination of tone/finish/pattern vs. skin concerns
- **Decision layer** — full pipeline: skin read → judge → spend → plan; budget exhaustion; empty input
- **Client** — mocked upload, submit, poll, error handling, convenience wrappers

## Licence

MIT — see [LICENSE](LICENSE).
