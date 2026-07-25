# Milestone 4: FastAPI API Layer Design

**Date:** 2026-07-25  
**Branch:** `feature/m4-api`

## Goal

Expose M1–M3 as REST API. FastAPI is HTTP-only; RAG stays in existing modules.

## Decisions

| Topic | Choice |
|-------|--------|
| `best_distance` | `float \| None` |
| Empty question/query | `min_length=1` → 422 |
| Search `debug` | Omitted when DEBUG is false |
| Startup | Lifespan preloads embedding + Chroma |

## Layout

`app/api/routes.py`, `app/models/*`, `app/services/*` thin wrappers over `answer_question` / `search`.
