# Foundation and Configuration Boundaries

Something belongs in the Reusable Foundation only when **both** are true: it is already nearly identical across at least two real Knowledge Applications, **and** it varies only by configuration (not by a new strategy or domain behaviour). Feeling “more generic” is not enough—use this filter, not generality vibes. Vector search as an operation can be foundation; “if SKU missing, search same category” or “prefer clinical guidelines” cannot until they prove generic.

Configuration is split three ways: **`.env`** holds secrets only (API keys); **`config.yaml`** holds deployment/application parameters (models, chunking, retrieval knobs, collection names, app display name); **`prompts/`** holds domain behaviour as text files (not environment variables, not YAML blobs). Application code owns reusable strategies behind small interfaces; it does not absorb persona or business rules.

Default Domain Layer language for the template is **neutral Indonesian** (usable guardrails and prompts without a company/persona). Per-app locale switching is deferred until a second application needs it.

Forks and clones take **source and domain files** (code, `prompts/`, `config/`, tests, docs). They do not take secrets, local `chroma_db/`, or uploaded/generated document corpora as source of truth—those are rebuilt by re-ingest. Optional versioned **sample** documents for demo/tests may live under a deliberate sample path; runtime document storage stays out of git.

