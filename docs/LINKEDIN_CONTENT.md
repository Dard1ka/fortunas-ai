# LinkedIn Content — Fortunas AI

Copy-paste ready content for LinkedIn profile and activity posts.
Customize the [brackets] before publishing.

---

## 🧑‍💼 PROFILE UPDATES

### Headline (pick one)
```
Full-Stack AI Developer | Built Fortunas AI — Conversational BI for 65M Indonesian MSMEs
```
```
Computer Science @ Binus University | RAG · FastAPI · React · BigQuery | MIS Student Grant 2026
```

### About Section (add to existing bio)
```
🚀 Currently building Fortunas AI — a conversational business intelligence platform
that lets Indonesian UMKM owners ask their sales data questions in plain Bahasa Indonesia,
powered by RAG (Retrieval-Augmented Generation), a local LLM (Qwen3:8b via Ollama),
and Google BigQuery as the analytics warehouse.

Tech: FastAPI · React 19 · ChromaDB · sentence-transformers · APScheduler · Google Sheets
```

### Skills to Add
- Retrieval-Augmented Generation (RAG)
- Large Language Models (LLM)
- FastAPI
- Google BigQuery
- React.js
- ChromaDB
- Natural Language Processing (NLP)
- Data Pipeline Engineering
- Python (Advanced)

### Featured Project (Project Section)
```
Title:   Fortunas AI — Conversational Business Intelligence for Indonesian MSMEs
URL:     https://github.com/YOUR_USERNAME/fortunas-ai

Description:
An AI-powered analytics platform for Indonesian MSMEs (Usaha Mikro, Kecil, Menengah).
Business owners type questions in natural Bahasa Indonesia — Fortunas AI queries BigQuery,
retrieves domain context via RAG (ChromaDB + sentence-transformers), and generates
structured business insights using a locally hosted Qwen3:8b LLM via Ollama.

Key features: 4 auto-intent analyses (repeat customer, high-value, peak hour, bundle
opportunity) · WhatsApp-style chat simulator · dual-layer staging (Google Sheets → BigQuery)
· daily auto-briefing · full data privacy (LLM runs locally, zero token cost).

MIS Student Grant 2026 · Binus University
```

---

## 📢 ACTIVITY POSTS

### Post 1 — Project Launch Announcement
**Timing:** Day you push to GitHub

```
🎉 Excited to share Fortunas AI — a project I've been building with my team for the
MIS Student Grant 2026 at Binus University.

The problem we're solving:
Indonesia has 65 million MSMEs contributing 61% of GDP — yet most can't afford
a data analyst or BI tool. They have transaction data but no insight layer.

Our solution:
Fortunas AI lets UMKM owners ask their data questions in plain Bahasa Indonesia.
No SQL. No dashboards. Just type — and get a structured business insight back in seconds.

Under the hood:
→ FastAPI backend with async pipeline
→ Google BigQuery as the analytics warehouse
→ RAG (Retrieval-Augmented Generation) with ChromaDB
→ sentence-transformers (multilingual) for embeddings
→ Qwen3:8b via Ollama — fully local LLM, zero token cost
→ WhatsApp-style chat simulator in React 19
→ Google Sheets as audit trail + staging layer

Ask it: "Pelanggan mana yang paling sering beli?" and it queries BigQuery,
pulls context from ChromaDB, and generates a full insight report — in under 5 seconds.

GitHub: [link]

#AI #MachineLearning #RAG #FastAPI #React #BigQuery #UMKM #Indonesia #StudentProject
```

---

### Post 2 — Technical Deep-Dive
**Timing:** 3–5 days after launch post

```
🔍 A technical breakdown of how Fortunas AI works under the hood.

The trickiest design decision: how do you make an LLM answer business questions
accurately WITHOUT hallucinating data?

The answer: Retrieval-Augmented Generation (RAG) — and here's our exact pipeline:

1️⃣ Intent Classification
   User types a natural language question.
   We map it to one of 4 intents: repeat_customer · high_value_customer
   · peak_hour · bundle_opportunity

2️⃣ Semantic Retrieval
   The question is embedded with paraphrase-multilingual-MiniLM-L12-v2
   (works natively in Bahasa Indonesia + 50 other languages).
   Top-5 relevant UMKM knowledge docs retrieved from ChromaDB.

3️⃣ SQL Execution
   Each intent maps to a parameterized BigQuery query.
   Real data, no fabrication.

4️⃣ Prompt Assembly
   Retrieved context + SQL results → structured prompt for the LLM.

5️⃣ Local LLM Generation
   Qwen3:8b (Ollama) generates the final insight in Bahasa Indonesia.
   Fully offline. Zero API cost. Data never leaves the server.

6️⃣ Dual-Layer Staging (for transactions)
   Input → Pydantic validation → Google Sheets (audit) → BigQuery INSERT
   APScheduler retries failed rows automatically.

The whole pipeline runs in < 5 seconds on a consumer GPU.

What I learned: architecture > model size. A well-designed RAG pipeline with
a 8B local model beats a bloated GPT-4 call with no context grounding.

GitHub: [link]

#RAG #LLM #FastAPI #BigQuery #Python #AIEngineering #MachineLearning
```

---

### Post 3 — Results / Reflection (after demo/testing)
**Timing:** After user testing or demo presentation

```
📊 Fortunas AI — what we built, what we learned, what's next.

After [X] weeks of building, here's where we landed:

✅ What works (MVP):
• Natural language query → BigQuery analytics → LLM insight in < 5 seconds
• WhatsApp-style chat simulator in React (no WA API needed for MVP)
• 4 automated analyses: repeat customer, high-value, peak hour, bundle opportunity
• Daily business briefing via APScheduler cron
• 1M+ row UCI Online Retail dataset successfully ingested & queried

📌 What we're honest about:
• Real WhatsApp integration is scoped for the next phase
  (Meta Cloud API region restriction in MVP — infrastructure is ready)
• LLM responses in Indonesian are good, not perfect
• User testing with actual UMKM owners is the next critical step

💡 Biggest learning:
Don't underestimate the staging layer.
Our Google Sheets → BigQuery dual pipeline with auto-retry saved us multiple times
when network failures would otherwise have caused silent data loss.

What would you prioritize next — WhatsApp integration or better LLM fine-tuning?

GitHub: [link]

#BuildInPublic #AIStartup #UMKM #Indonesia #RAG #StudentProject #MISGrant
```

---

## 📌 ENGAGEMENT TIPS

1. **Tag teammates** in the launch post — more reach, shows teamwork
2. **Reply to every comment** in the first 2 hours (LinkedIn algorithm rewards early engagement)
3. **Add the GitHub link** as a Featured post on your profile
4. **Connect with UMKM / startup ecosystem** people in Indonesia after posting
5. **Cross-post a shorter version** as a LinkedIn Article for permanent SEO value

---

## 🏷 Hashtag Sets

**Technical:** #RAG #LLM #FastAPI #BigQuery #ChromaDB #Python #React #AI #MachineLearning #NLP

**Audience:** #UMKM #Indonesia #StudentProject #MISGrant #BinusUniversity #BuildInPublic

**Career:** #ComputerScience #FullStack #SoftwareEngineering #DataEngineering
