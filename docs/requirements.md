### 1. Problem & Goal

Keeping tabs on dozens of applications in spreadsheets or memory is error-prone. A Discord bot that lives where you already spend time can:

* capture every application event in seconds (`/applied`, `/oa_completed`, `/interview_done`)
* surface next actions and deadlines (`/todo`, automated DM reminders)
* show progress analytics (e.g., “5 apps in OA, 3 awaiting recruiter reply”)

**Goal:** Ship an MVP bot that lets a single user (you) log and query application stages from any Discord server or DM, backed by a zero-config local database.

---

### 2. Success Metrics (90-day MVP)

| Metric                                | Target                    |
| ------------------------------------- | ------------------------- |
| Avg. command round-trip latency       | < 1 s                     |
| Setup time (clone → working bot)      | ≤ 10 min                  |
| Manual spreadsheet updates eliminated | 100 %                     |
| Reminder delivery accuracy            | ≥ 95 % of scheduled times |
| Code coverage (unit tests)            | ≥ 70 %                    |

---

### 3. Personas

* **Primary:** Angel – Data engineer & intern hunter, commands the bot via slash commands.
* **Secondary (stretch):** Friends/grads who join the server and want the same tracker; each gets isolated data.

---

### 4. Scope

#### Must-Have Functional (launch)

1. **Add application** – `/add <company> <role>` → stage defaults to “Applied”.
2. **Update stage** – `/update <company> <stage> [date]` stages: Applied → OA → Phone → On-site → Offer → Rejected.
3. **List / filter** – `/list [stage]` shows paginated summary.
4. **Next-steps summary** – `/todo` returns apps without activity > 7 days.
5. **Reminders** – opt-in per app (`/remind <company> <days>`) → DM on due date.
6. **Analytics** – `/stats` pie-chart counts by stage + recent velocity (commands return ASCII bar chart in MVP).

#### Nice-to-Have (post-MVP)

* Multi-user / guild support.
* Export CSV / JSON.
* Webhook to push updates to Notion / Airtable.
* Interview prep checklist generator.

#### Out-of-Scope

* Resume parsing, OA auto-imports, AI feedback on interviews.

---

### 5. Non-Functional Requirements

* **Setup friction:** pip install + environment vars + one `python main.py`.
* **Portability:** runs on Windows, macOS, Linux; can be Heroku/Fly.io deployed.
* **Privacy:** data stored locally by default; no external APIs needed.
* **Reliability:** graceful restart without data loss; idempotent commands.
* **Extensibility:** clean command handler layer; DB schema migrations via Alembic optional.

---

### 6. Data Design (SQLite 3)

**Tables**

| Table        | Columns                                                            | Notes                                     |
| ------------ | ------------------------------------------------------------------ | ----------------------------------------- |
| applications | `id` PK, `company` TEXT, `role` TEXT, `created_at` DATETIME        | one row per job target                    |
| stages       | `id` PK, `app_id` FK → applications, `stage` TEXT, `date` DATETIME | stage history; latest row = current stage |
| reminders    | `id` PK, `app_id` FK, `due_at` DATETIME, `sent` BOOL               | one per scheduled nudge                   |

*Use a single `jobs.db` file inside project root. For “light & easy” this beats spinning up Postgres. If you later migrate, swap SQLAlchemy’s engine URL.*

---

### 7. Command Contract (Discord slash commands)

| Command   | Parameters                                 | Side-Effects                                        |
| --------- | ------------------------------------------ | --------------------------------------------------- |
| `/add`    | company, role                              | Insert into **applications**, stage “Applied”.      |
| `/update` | company, stage *(enum)*, date *(optional)* | Insert into **stages**.                             |
| `/list`   | stage *(optional)*                         | Read join **applications** ↔ **stages**.            |
| `/todo`   | —                                          | Compute stale apps (`now – last_update > 7d`).      |
| `/remind` | company, days\_until\_due                  | Insert into **reminders**.                          |
| `/stats`  | —                                          | Group-by stage count; return chart or text summary. |

---

### 8. System Architecture

```
Discord API ──(WebSocket)──▶ Bot Process (Python) ──▶ Command Router
                                                │
                                                ├─▶ Service Layer (business rules)
                                                │
                                                └─▶ SQLite (SQLAlchemy ORM)
Scheduler Thread (APScheduler) ── checks reminders ──▶ DM user
```

* **Language:** Python 3.12
* **Framework:** discord.py v2 (native slash commands)
* **Scheduler:** APScheduler (in-process cron)
* **ORM:** SQLAlchemy + Pydantic models
* **Packaging:** Poetry; `.env` for Discord token & path override
* **Testing:** pytest + pytest-asyncio; SQLite in-memory fixture
* **CI:** GitHub Actions (lint, tests)

---

### 9. Open Questions / Risks

1. **Multiple devices** – local SQLite on a laptop is fine for single-user; cloud deploy needs persistent volume or Postgres.
2. **Rate-limits** – analytics endpoints must chunk long messages (Discord 2000-char limit).
3. **Data privacy** – if hosted on shared server, encrypt `jobs.db` at rest?

---

### 10. Milestones & Timeline

| Week | Deliverable                                                   |
| ---- | ------------------------------------------------------------- |
| 1    | Project skeleton, `/add`, `/list`, SQLite models + migrations |
| 2    | Stage updates, `/update`, `/stats` (text)                     |
| 3    | Scheduler & `/remind`, `/todo`, persistence tests             |
| 4    | Analytics charts, error handling polish, README setup guide   |
| 5    | Public beta, feedback loop, backlog triage                    |

---

### 11. Handoff Package to Cursor

* `README.md` – quickstart (Python ≥3.12, `poetry install`, set `DISCORD_TOKEN`)
* `bot.py` – entry point
* `models.py`, `services.py`, `commands/`
* `jobs.db` (git-ignored)
* `schema.sql` for initial boot
* `.github/workflows/ci.yml`

---

### 12. Future Extensions

* Switch DB URL to `postgresql+psycopg://` via env var.
* Multi-guild support: add `guild_id` to **applications**.
* OAuth2 user auth for web dashboard.
* Integration with Trello / Notion for Kanban visualization.


