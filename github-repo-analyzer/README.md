# GitHub Repository Health Analyzer

A small Django web app that takes a public GitHub repository URL and
generates a **Repository Health Report**: basic repo information, a set of
simple automated health checks, an overall score out of 100, and a list of
suggestions for improving the repository.

Built as a portfolio project to demonstrate Django fundamentals: talking to
a third-party REST API, handling errors gracefully, storing results in
PostgreSQL, and rendering a clean, responsive frontend with plain HTML/CSS/JS
— no frontend framework.

---

## Features

- **URL input with validation** — paste a GitHub repository URL and get a
  clear error message if it isn't one.
- **GitHub API integration** — fetches repository metadata, the root file
  listing, and recent commits from the public GitHub REST API.
- **Health score (0–100)** — a transparent, rule-based score built from
  seven checks (see [How the score works](#how-the-score-works) below).
- **Health checks with explanations** — each check shows a status
  (pass / warning / fail) and a short, plain-language reason.
- **Suggestions** — generated automatically from any check that didn't
  fully pass.
- **Analysis history** — every analysis is saved to PostgreSQL and can be
  revisited later from the History page, without calling the GitHub API
  again.
- **Polished, responsive UI** — cards, a score ring, status badges, empty
  states, loading state, and error states, styled to look like a real
  developer tool rather than a school project.

---

## Technologies used

| Layer | Technology | Why |
|---|---|---|
| Backend | Python 3 + Django | The web framework — handles routing, forms, the ORM, templates. |
| Database | PostgreSQL | Stores every past analysis so the history page has something to show. |
| HTTP client | `requests` | Simplest way to call the GitHub REST API. |
| Config | `python-dotenv` | Loads secrets/config from a `.env` file instead of hardcoding them. |
| DB driver | `psycopg2-binary` | Lets Django talk to PostgreSQL. |
| Frontend | Django templates, plain HTML/CSS, vanilla JS | No frontend framework — kept simple on purpose. |

No Docker, no Celery/Redis, no microservices, no machine learning. This is
one Django project with one app.

---

## How the GitHub API is used

All GitHub API calls live in `analyzer/github_service.py`, in three small
functions:

1. `get_repository(owner, repo)` — `GET /repos/{owner}/{repo}`
   Basic repo info: stars, forks, open issues, language, license, size,
   and when it was last pushed to.
2. `get_root_contents(owner, repo)` — `GET /repos/{owner}/{repo}/contents`
   The list of files/folders in the repository root. Used to look for a
   README, a `tests`/`docs` folder, a `CONTRIBUTING` file, etc.
3. `get_recent_commits(owner, repo)` — `GET /repos/{owner}/{repo}/commits`
   The 10 most recent commits, used only to show a "recent commits
   checked" count.

Only public, unauthenticated-friendly endpoints are used — no repository
code is ever downloaded, cloned, or executed. A `GITHUB_TOKEN` is optional
and only raises the rate limit; the app works without one.

**Error handling.** `github_service.py` turns HTTP responses into one of
three exceptions, which `views.py` catches and turns into a friendly,
on-page error message instead of a stack trace:

- `RepositoryNotFoundError` — the repo doesn't exist, is private, or the
  URL was mistyped (GitHub returns `404`).
- `RateLimitExceededError` — GitHub's rate limit was hit (`403` with
  `X-RateLimit-Remaining: 0`).
- `GitHubAPIError` — anything else: a network problem, a timeout, or an
  unexpected status code.

---

## How the score works

The score is **rule-based and transparent** — there is no machine learning
involved. Seven checks each contribute points, adding up to a maximum of
100:

| Check | Points | Rule |
|---|---|---|
| README | 15 | Is there a file starting with `readme` in the repo root? |
| License | 10 | Does GitHub report a detected license? |
| Documentation | 15 | Is there a `docs` folder or a `CONTRIBUTING` file? (7 pts if only a README exists) |
| Tests | 15 | Is there a `tests`/`test`/`spec` folder, or files starting with `test_`, in the repo root? |
| Recent Activity | 20 | Was the repo pushed to in the last 90 days? (partial credit up to 365 days) |
| Repository Size | 10 | Is the repo non-empty and not absurdly large? |
| Issues | 15 | Are open issues at a manageable count (≤ 50 for full credit)? |

The logic for every check is in `analyzer/health_score.py`, as small,
readable functions — each one is a handful of `if`/`elif` statements. This
is deliberate: the whole point of the "health score" is that anyone can
open that file and see exactly why a repository got the score it did.

### Honest limitations

This is a **simple, automated indicator** — not a code quality audit. In
particular:

- The tests/docs checks only look at the **repository root**. A project
  that keeps its tests in a nested folder, or documents itself entirely on
  a wiki or external site, may be marked down unfairly.
- "Recent activity" only measures the last push date. A repository can be
  well-maintained with infrequent commits.
- The "Issues" check doesn't distinguish between a healthy, actively
  triaged backlog and a neglected one — it only counts how many are open.
- License and README detection rely entirely on GitHub's own metadata and
  file-naming conventions.

The score is meant as a useful starting point for a conversation about a
repository, not a final verdict.

---

## Project structure

```
github-repo-analyzer/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── config/                    # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── analyzer/                  # The one Django app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py              # RepositoryAnalysis model
│   ├── forms.py                # URL validation
│   ├── github_service.py      # All GitHub API calls
│   ├── health_score.py        # All scoring/health-check logic
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
├── templates/
│   ├── base.html
│   └── analyzer/
│       ├── home.html
│       ├── dashboard.html
│       └── history.html
└── static/
    └── analyzer/
        ├── css/style.css
        └── js/main.js
```

---

## Installation

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 13+ installed and running locally (or accessible over the network)

### 2. Clone/copy the project and create a virtual environment

```bash
cd github-repo-analyzer
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

Create a database and a user for the project (run inside `psql`, or however
you normally manage PostgreSQL):

```sql
CREATE DATABASE repo_analyzer;
CREATE USER repo_analyzer_user WITH PASSWORD 'choose-a-password';
GRANT ALL PRIVILEGES ON DATABASE repo_analyzer TO repo_analyzer_user;
```

(If you already have a local PostgreSQL superuser, e.g. `postgres`, you can
skip creating a new user and just create the database.)

### 5. Configure environment variables

Copy the example file and fill in your own values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=<generate a long random string>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=repo_analyzer
DB_USER=repo_analyzer_user
DB_PASSWORD=choose-a-password
DB_HOST=localhost
DB_PORT=5432

# Optional — raises the GitHub API rate limit from 60 to 5,000 requests/hour.
# Create one at https://github.com/settings/tokens (no special scopes needed
# for public repositories).
GITHUB_TOKEN=
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. (Optional) Create an admin user

```bash
python manage.py createsuperuser
```

This lets you browse saved analyses at `/admin/`.

### 8. Run the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** in your browser.

---

## How to test the major features

1. **Home page & validation**
   Go to `/`. Try submitting the form with something that isn't a GitHub
   URL (e.g. `hello`) — you should see a field-level error and no request
   to GitHub is made.

2. **Analyzing a repository**
   Enter `https://github.com/django/django` (or click the "django/django"
   quick-fill button) and click **Analyze**. You should be redirected to a
   report page showing repository info, a score ring, seven health checks,
   and a suggestions list.

3. **Error handling**
   Try a repository that doesn't exist, e.g.
   `https://github.com/this-user-does-not-exist-xyz/nope`. You should see a
   clear on-page error message, not a crash page.

4. **History**
   Go to `/history/`. You should see every repository you've analyzed,
   with its score, star count, and the date it was analyzed. Click a row
   to view that report again — it loads instantly from the database
   instead of calling the GitHub API again.

5. **Admin (optional)**
   If you created a superuser, visit `/admin/` and look at the
   "Repository analyses" table to see the raw stored data, including the
   JSON `checks` and `suggestions` fields.

---

## Architecture overview

This is a standard Django MVT (Model-View-Template) app with exactly one
app, `analyzer`, to keep things simple:

- **`models.py`** defines one model, `RepositoryAnalysis`, which stores
  everything about one analysis — including the health checks and
  suggestions as JSON, so a past result can be shown again without calling
  the GitHub API a second time.
- **`forms.py`** validates and parses the submitted URL into an
  `owner`/`repo` pair using a single regular expression.
- **`github_service.py`** is the only file that knows how to talk to
  GitHub. It has no knowledge of Django models or templates — it just
  returns plain dicts/lists or raises one of three exceptions.
- **`health_score.py`** is the only file that knows how to turn GitHub
  data into a score. It has no knowledge of the GitHub API or the
  database — it's pure functions that take data in and return a score,
  checks, and suggestions.
- **`views.py`** ties the two services together: it validates the form,
  calls `github_service` and `health_score`, saves a `RepositoryAnalysis`,
  and redirects to the report page (a **POST/redirect/GET** pattern, so
  reloading a report page never re-runs the analysis).
- **Templates** are plain Django templates extending a shared `base.html`.
  There's no JavaScript framework — the one `main.js` file just adds a
  loading state to the Analyze button and wires up two "try this repo"
  quick-fill buttons.

This separation means each file answers one question: "what does GitHub
say?", "how healthy is that?", or "what does the user see?" — which keeps
each one small enough to read top-to-bottom.

---

## Known limitations & future improvements

**Current limitations:**

- Health checks only look at the repository root, not the full file tree
  (see [Honest limitations](#honest-limitations) above).
- No user accounts — history is shared by everyone using the app (fine for
  a portfolio/demo project, not for a multi-user product).
- No background processing — an analysis runs synchronously during the
  request, so a slow or rate-limited GitHub API call makes the page wait.
- No automated test suite is included in this initial version.
- Without a `GITHUB_TOKEN`, the app is limited to 60 GitHub API requests
  per hour per IP address, which is easy to hit while testing.

**Possible future improvements:**

- Add a proper Django test suite (`pytest-django` or `unittest`, mocking
  the GitHub API) to lock in current behavior before making changes.
- Recursively scan a few directory levels deep for tests/docs, instead of
  only the repository root.
- Cache results for a short time (e.g. 1 hour) so re-analyzing the same
  popular repository doesn't immediately re-hit the GitHub API.
- Add simple user accounts so each person sees only their own history.
- Move the GitHub API calls into a background task (e.g. with
  `django-q` or Celery) if the app ever needs to analyze many repositories
  in bulk.
- Compare a repository's score against similar repositories for more
  useful context than a bare number.

---

## Security notes

- All secrets (the Django `SECRET_KEY`, database credentials, and the
  optional `GITHUB_TOKEN`) are read from environment variables via a
  `.env` file, which is excluded from version control by `.gitignore`.
- Django's CSRF protection is enabled by default and used on the analyze
  form.
- User input (the repository URL) is validated with a strict regular
  expression before any GitHub API call is made.
- The app never clones, downloads, or executes any code from the analyzed
  repository — it only reads metadata through GitHub's REST API.
