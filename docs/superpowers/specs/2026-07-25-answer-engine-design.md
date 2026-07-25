# Milestone 3: Answer Engine Design

**Date:** 2026-07-25  
**Branch:** `feature/m3-answer` from `main`

## Goal

Compose answers from retrieved chunks via Groq. The LLM never decides relevance or citations — the backend filters by distance and attaches sources from metadata.

## Decisions

| Topic | Choice |
|-------|--------|
| Distance threshold default | **25.0** (L2 scale; tunable via `.env`) |
| Sources | Dedup `(document, page)`, order by best rank |
| Missing `GROQ_API_KEY` | Raise clear error (CLI non-zero) |
| Architecture | `prompts.py` / `llm.py` / `answer.py` separation |
| Guardrail (no chunks pass) | Fixed Indonesian message; **no Groq call** |

## Pipeline

`search` → filter `distance <= threshold` → (empty → guardrail) → `build_prompt` → `call_groq` → attach sources → structured dict (`confidence=None`).

## Modules

- `config.py`: `retrieval_distance_threshold`, `groq_api_key`, `groq_model` (`llama-3.3-70b-versatile`)
- `prompts.py`: `build_prompt(question, chunks)` only
- `llm.py`: `call_groq(prompt) -> str` only
- `answer.py`: `answer_question` + CLI + logging/timings

## Non-goals

No FastAPI/UI. No confidence scoring.
