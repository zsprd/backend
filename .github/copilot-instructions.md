# Copilot Instructions for ZSPRD Portfolio Analytics Backend

## Project Overview

-   **Domain:** Professional portfolio analytics for high-net-worth individuals
-   **Stack:** FastAPI (Python 3.11+), SQLAlchemy ORM, Alembic migrations, PostgreSQL, JWT Auth, Alpha Vantage integration
-   **API Structure:** Versioned under `/api/v1/` (see `app/api/v1/`)
-   **Major Components:**
    -   `app/core/`: Config, DB, Auth
    -   `app/models/`: SQLAlchemy models & enums
    -   `app/schemas/`: Pydantic schemas (input/output validation)
    -   `app/crud/`: Data access logic
    -   `app/services/`: Business logic (analytics, calculations)
    -   `app/api/v1/`: API endpoints (accounts, analytics, etc.)
    -   `app/utils/`: Utility functions (rate limiting, calculations)

## Key Patterns & Conventions

-   **Enum Handling:**
    -   All enums (e.g., `AccountCategory`) use lowercase string values for DB and API compatibility.
    -   Pydantic schemas use model-level validators to coerce string values to enums.
    -   When returning ORM objects, always convert to Pydantic models using `model_validate(obj, from_attributes=True)` to ensure enum and type correctness.
-   **Authentication:**
    -   JWT tokens required for all endpoints except health checks.
    -   User ID is extracted from the JWT `sub` claim (see `app/core/user.py`).
-   **Error Handling:**
    -   API endpoints raise `HTTPException` with clear messages and status codes.
-   **Database:**
    -   Alembic for migrations (`alembic/`), see README for migration commands.
    -   Models in `app/models/`, enums in `app/models/enums.py`.
-   **Testing:**
    -   Tests are in `tests/` (e.g., `test_api_example.py`).
    -   Run with `pytest -v`.
-   **Formatting & Linting:**
    -   Use `black`, `isort`, and `flake8` (see README for commands).

## Developer Workflows

-   **Run API:** `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
-   **Run Tests:** `pytest -v`
-   **Migrations:**
    -   `alembic revision --autogenerate -m "msg"`
    -   `alembic upgrade head`
-   **Environment:**
    -   Copy `.env.example` to `.env` and fill in secrets (see README)

## Integration Points

-   **Alpha Vantage:** Market data via `app/utils/alpha_vantage.py` (rate-limited, cached)
-   **Frontend:** NextJS, expects JWT in `Authorization` header

## Examples

-   **Enum pattern:** See `app/models/enums.py` and `app/schemas/account.py`
-   **Account endpoint:** See `app/api/v1/accounts.py` for explicit ORM→Pydantic conversion

## Special Notes

-   Always use lowercase for enum values in DB and API
-   When adding new endpoints, follow the pattern of explicit Pydantic conversion for ORM objects
-   Use `from_attributes=True` with Pydantic v2 for ORM serialization

---

For more, see `README.md` and code comments in each module.
