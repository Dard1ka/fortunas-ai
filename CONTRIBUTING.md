# Contributing to Fortunas AI

Thank you for your interest in contributing! This guide covers conventions and workflow for the Fortunas AI team.

---

## 🔀 Branch Strategy

```
main          ← stable, always deployable
dev           ← integration branch (merge PRs here first)
feat/<name>   ← new feature
fix/<name>    ← bug fix
docs/<name>   ← documentation only
```

Always branch off `dev`, never commit directly to `main`.

## 📝 Commit Convention (Conventional Commits)

```
feat:     new feature
fix:      bug fix
docs:     documentation change
refactor: code change (no feature / bug)
test:     add or update tests
chore:    tooling, CI, dependencies
```

Examples:
```
feat: add bundle_opportunity intent handler
fix: retry scheduler skipping failed rows after restart
docs: update SETUP.md with GPU requirements for Qwen3
```

## 🏗 Module Ownership

| Module | Owner | Key Files |
|---|---|---|
| Backend API + Pipeline | Darrel | `app/api/routes/`, `app/core/`, `app/services/pipeline.py` |
| SQL Agent + BigQuery | Steven | `app/agents/sql_agent.py`, `app/queries.py`, `app/bigquery_service.py` |
| RAG Agent + Embeddings | Filo | `app/agents/rag_agent.py`, `app/knowledge/ingest.py` |
| Insight Agent + LLM | Michael | `app/agents/insight_agent.py`, `app/llm_service.py`, `app/prompt_builder.py` |
| Frontend (React) | Darrel | `frontend/src/` |

For cross-module changes, open a PR and request review from the module owner.

## ✅ Before Pushing

- [ ] `pip install -r requirements.txt` still works clean
- [ ] `uvicorn app.main:app` starts without error
- [ ] `npm run build` in `frontend/` passes
- [ ] No `.env` or `*.json` credentials in staged files: `git diff --cached --name-only`
- [ ] `requirements.txt` updated if you added new imports: `pip freeze > requirements.txt`

## 🚫 Never Commit

- `.env` (real credentials)
- `credentials/*.json` (service account)
- `chroma_db/` (local vector store)
- `frontend/node_modules/` or `.venv/`
- Any file containing real API tokens or phone numbers
