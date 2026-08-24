# Phase D: Portfolio Story (How it works + Case study)

**Status:** Approved  
**Date:** 2026-08-23

## Goal

Help portfolio visitors understand what they are looking at: RAG pipeline, guardrails, eval results, and trade-offs — without leaving the chat demo.

## UX

- Nav link **About** (portfolio mode only) opens a slide-over panel
- Sections: Problem, Pipeline, Guardrails, Live stats, Eval snapshot, Trade-offs
- Live stats from `/api/v1/stats`; narrative from config `about:` block
- Eval metrics from config (updated when re-run eval)

## API

`GET /api/v1/about` → `{ show, ...about fields, stats: { documents, chunks } }`

## Non-goals

- Separate route/page (stay single-page for subdomain deploy)
- PDF viewer
