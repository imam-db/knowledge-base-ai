# Phase C: UX Polish

**Status:** Approved (continue from roadmap)  
**Date:** 2026-08-23  
**Product:** Knowledge Base AI

## Goal

Make the portfolio chat feel like a product: clearer sources, explicit answer states, shareable questions, and streamed answers.

## Scope

1. **Sources UX** — Hide `chunk_id` / `distance` from the default UI. Show `document · Page N` and a short text snippet (from retrieval/search enrichment). Optional “Technical details” disclosure for distance.
2. **Answer status** — Each assistant message tagged `answered` | `not_found` | `error`. Drive from empty sources / guardrail text / transport errors. Small badge on the bubble.
3. **Shareable `?q=`** — On load, if `?q=` present, auto-send once. “Copy link” updates the URL / clipboard with the last question.
4. **Streaming** — `POST /api/v1/ask/stream` (SSE). Events: `status`, `sources`, `token`, `done`, `error`. Keep non-streaming `POST /ask` for tests/CLI.

## Non-goals

- PDF page viewer / iframe handbook (later)
- Auth, rate limit (Phase E)
- How-it-works / case study page (Phase D)

## Acceptance

- Example question streams tokens without waiting for full completion
- Not-found answers show a distinct badge and no misleading sources
- Opening `/?q=When+does+the+Winter+Transfer+Window...` runs that question
- Existing `POST /ask` tests still pass
