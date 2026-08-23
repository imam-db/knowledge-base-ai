# Knowledge Application

An AI application built for one knowledge domain: ingest documents, retrieve relevant passages, and generate grounded answers with citations.

## Language

**Knowledge Application**:
One AI application built for one knowledge domain (for example SOP/policy, clinic procedures, or a product catalog).
_Avoid_: RAG product, RAG app, knowledge base (as the genre name)

**RAG**:
The retrieval-augmented generation mechanism used inside a Knowledge Application (ingest → embed → retrieve → generate).
_Avoid_: Using "RAG" as the name of the product or the unit of reuse

**Knowledge Base AI**:
The first Knowledge Application in this lineage: internal company SOP / policy / FAQ. After the template baseline is tagged, it lives in its own product repository forked from the template.
_Avoid_: Treating this name as the genre for all future apps; keeping it as a dual identity inside the template repo

**Reusable Foundation**:
The cloneable parts of a Knowledge Application that stay boring across domains (ingestion, embedding, retrieval, vector store, LLM interface, API, auth pattern, thin UI shell). Something belongs here only when it is already nearly identical across at least two real Knowledge Applications **and** varies only by configuration, not by a new strategy or behaviour.
_Avoid_: rag-core (as a package name until extraction is justified), framework, junk-drawer utilities

**Domain Layer**:
The parts that give a Knowledge Application its character: prompts, persona, business rules, domain metadata, retrieval strategy, branding, and terminology. Lives outside the foundation (for example `prompts/`, domain config values, business rules).
_Avoid_: Stuffing domain behaviour into the foundation because it "could" be a function

**Template baseline** (`template-v1`):
A tagged, renamed, runnable skeleton of this codebase with **neutral Indonesian** Domain Layer defaults (generic app name and prompts), not a framework rewrite. Requires config split, thin provider interfaces, green tests, and clone documentation before the tag.
_Avoid_: Using the baseline as an excuse for large structural refactors; blocking the tag on frontend config plumbing perfection
