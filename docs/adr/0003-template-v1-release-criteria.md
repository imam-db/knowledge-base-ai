# Template-v1 Release Criteria

`template-v1` is tagged only after this repo has been cleaned into a runnable Knowledge Application template—not rewritten into a framework. Required before rename + tag + fork: (1) `.env` / `config.yaml` / `prompts/` split with neutral Indonesian domain defaults; (2) thin `LLMProvider`, `EmbeddingProvider`, and `ChromaStore` interfaces under `app/core/` wired into the existing app with tests green; (3) README clone guide plus complete `.env.example` and sample `config.yaml`.

Not required to block the tag: frontend reading `app.name` from a single API/config source. Hardcoded product branding in the UI must still be neutralized for the template, but the exact wiring can be simple. After the tag, rename to `knowledge-application-template`, then fork `knowledge-base-ai` as product #1 with domain overlays and re-ingest—no shipping of `.env` or `chroma_db/`.
