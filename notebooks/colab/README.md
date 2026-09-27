# Colab evaluation placeholders (fenced)

**Status:** Placeholder path only — **not** Mesh runtime.  
**Authority:** ChatGPT `APPROVE_WITH_FENCES` (`council/CHATGPT_REPLY_GOOGLE_AI_TOOLS_APPROVAL.md`).  
**Note:** `council/NOTE_GOOGLE_AI_TOOLS_FENCED.md`.

## Purpose

Optional home for **offline** Colab / local notebooks used for:

- scorecard / eval harness experiments
- reproducibility checks
- research analysis of mock L_judge / Gemini-peer digests

## Fences

- **No Colab login required** to keep this directory in-repo or to run CI.
- Notebooks here are **evaluation artifacts**, not production state, control plane, or execution layer.
- Do **not** embed API keys, Mesh operational secrets, or live enablement switches.
- **live=DISABLED**; Google tools do not replace Neural Mesh orchestration.

## Future

Add `.ipynb` files under this directory when operators want offline harnesses. Until then this README is the path note only.
