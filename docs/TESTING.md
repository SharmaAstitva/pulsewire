# Testing Strategy

PulseWire has **107 automated tests**: 78 for the backend and 29 for the frontend. They run on every push
through GitHub Actions, and the build fails if backend coverage drops below 90%.

| Suite | Unit | Integration | Coverage |
|---|---|---|---|
| Backend (pytest) | 48 | 30 | 96% of lines |
| Frontend (Vitest + Testing Library) | 10 | 19 | 96% of lines |

## The two layers

**Unit tests** check one function or component in isolation. They have no database and no network, and the
whole backend unit suite runs in under a second.

- Backend `tests/unit/`: text cleaning, URL normalisation, date parsing, image extraction, title cleaning,
  story clustering, trending maths, both AI backends (HuggingFace models replaced by stubs, the Groq API
  replaced by `httpx.MockTransport`), response schemas, and the rate limiter (with an injected fake clock).
- Frontend `src/__tests__/unit/`: the debounce hook (fake timers), the API client's error handling, and the
  article card.

**Integration tests** check that real pieces work together.

- Backend `tests/integration/`:
  - the full pipeline against a real SQLite database, including a broken feed, idempotent re-runs and archiving
  - every API endpoint over HTTP, plus CORS, rate limiting, pagination and validation errors
  - **snapshot sync against a real local HTTP server** that supports ETags: download, 304 handling,
    rejecting a corrupted file while keeping the old data, and the API starting when the server is unreachable
  - **the command-line pipeline run as a real subprocess**, fetching RSS feeds over HTTP from a local server,
    then the API serving the database it produced
  - upgrading a database created by an older version of the schema
- Frontend `src/__tests__/integration/`: real components, React Query and React Router together, with only
  the HTTP layer faked. Covers the news feed (pagination, category switching, error and empty states),
  search, the article page, and **the whole app**: loading the front page, debounced search, clicking
  through to an article, and filtering by topic.

## Test-driven development

New features and bug fixes were built test-first: write a failing test (**red**), write the minimum code to
pass it (**green**), then clean up with the tests as a safety net (**refactor**). The code that existed before
this was tested afterwards. Those tests are kept, but they are not counted as TDD.

| # | Red: the failing test | Green: the change |
|---|---|---|
| 1 | Searching for `%%` returned **every** article, because `%` was treated as a SQL wildcard | Escape `%`, `_` and `\` in search terms |
| 2 | Headlines like "… - BBC News" didn't cluster with the same story from other outlets | `clean_title()` strips a trailing publisher name |
| 3 | One article crashing the AI model failed the **entire** pipeline run | Fall back to the lite analyser for that article and count the failure |
| 4 | A database created before a new column existed would crash the pipeline | Forward-only migration that adds missing columns |
| 5 | Rate limiting was **silently not working**: 130 requests in a row all succeeded | Replaced slowapi with a small tested limiter (see below) |
| 6 | After "Load more", switching topic kept showing the **previous topic's** stories | Reset the feed's pages when the category changes |

Cycles 1, 5 and 6 were real bugs that no manual testing had caught.

### The rate-limiting bug

The integration test sent 125 requests and expected a `429 Too Many Requests`. It got 125 successes.
Investigation showed that newer FastAPI versions wrap included routers in a new internal type, so the
`slowapi` middleware could no longer find any route handler and **exempted every request without any error**.
The fix was a 40-line fixed-window limiter with its own unit tests (fake clock, per-client counting,
window reset, memory clean-up) and integration tests (429 status, `Retry-After` header, CORS headers kept on
429 responses, health check exempt).

## Checking the tests themselves

Passing tests only matter if they would fail when the code is wrong. As a spot check (manual mutation
testing), deliberate bugs were introduced and the suite was confirmed to catch each one:

- removing the search debounce → the full-app search test fails
- always showing the "N sources" badge → the article card test fails
- listing the current article in its own "related" sidebar → the article page test fails
- removing the category reset → the news feed test fails

## Running the tests

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
pytest                        # everything
pytest -m unit                # fast unit tests only
pytest -m integration         # integration tests only
pytest --cov=app --cov=pipeline --cov-report=term-missing

# Frontend
cd frontend
npm install
npm test                      # all tests
npm run test:watch            # re-run on save (handy for TDD)
npm run test:coverage
```

## Not covered yet

- **The real HuggingFace models** are not loaded in tests. They take gigabytes and minutes to download. The
  code around them is tested with stubs, and the scheduled pipeline run exercises the real models.
- **Live news feeds** are not called. Tests use recorded RSS fixtures, so results never depend on the news.
- **End-to-end browser tests** (for example Playwright running the real frontend against the real API) would
  be the next layer to add.
