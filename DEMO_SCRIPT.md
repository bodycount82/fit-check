# Fit Check — demo script (2:50)

For the YouCam hackathon submission video. Read this aloud while running `python demo.py`.

---

## 0:00 — Open the terminal, run the demo

```bash
cd fit-check
python demo.py
```

> "This is Fit Check — an advisor that decides what is worth rendering, and refuses the rest."

## 0:15 — Explain the problem

> "Everything YouCam sells is generative: it renders what you ask for. But nobody upstream of the render is qualified to ask. People try on the wrong things, and returns are driven by 'it looked different on me.' So we built the part the API does not do."

## 0:35 — Walk the output

> "The demo profile simulates a person with elevated redness and texture — two common concerns. The skin analysis costs 22 units. That buys every decision below it."

> "The advisor evaluates six candidate items. It refuses four: the warm-toned rust blazer because it amplifies redness, the satin blouse because high sheen contrasts with uneven texture, the floral dress because busy patterns draw attention to pores, and the metallic top for the same reason."

> "It keeps two: the cool-toned, matte-finish slate shirt and navy jacket. No rule fired against them."

## 1:00 — Explain the budget

> "The unit budget is visible. 22 units for the skin read, 2 per render. The full decision trail shows exactly what was spent, why, and what was left. This is not a black box — it's a decision with receipts."

## 1:20 — Explain the architecture

> "The repo has three layers. The API client is thin and honest — auth, upload, submit, poll. The decision layer reads the skin profile, asks the advisor about every candidate, and spends a visible budget. The advisor is pluggable: the published repo ships a rule-based reference implementation so judges can run it with no key and no network. An optional private drop-in can swap in a different brain."

## 1:50 — Explain the UI

> "The Streamlit UI shows the same thing as a product, not a demo: two columns — chosen and refused — each with the reason. The budget meter shows what was spent. The decision trail is expandable."

## 2:10 — Explain why this wins on Criterion 4

> "Criterion 4 asks for a creative, non-obvious use of the YouCam API. The obvious submission is 'an agent that calls the YouCam tools' — which Perfect Corp already ships as hosted MCP servers with 99 tools. So the integration is a configuration file. The decision layer is the whole product. A refusal is the one output an image generator cannot produce, so it can't be confused with the vendor's own getting-started page."

## 2:35 — Close

> "Fit Check is a decision, not a render. It's the part the API does not do. Thank you."

---

## Technical notes for the recording

- Run `python demo.py` — no API key needed, no network, no Genesis.
- The output is deterministic: same skin profile, same catalogue, same refusals every time.
- If you want to show the UI: `streamlit run app.py` — but the terminal demo is sufficient and more reliable for recording.
- The demo profile simulates: redness 68, texture 61, oiliness 52 (elevated above 55).
- The catalogue has 6 items with attributes the advisor can reason about: tone (warm/cool/rust), finish (matte/satin/metallic), pattern (solid/floral).
