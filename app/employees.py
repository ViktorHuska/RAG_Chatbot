"""Demo employee profiles, in SQLite.

Without a known employee, most handbook questions have no single right answer.
"How much PTO do I get?" depends on which legal entity employs you and how long
you have been there; "what am I paid for on call?" depends on the country. The
bot has to hedge or ask. With a profile it can answer once, exactly.

The personas are chosen to land on opposite sides of the corpus's traps — every
one of them gets a different correct answer to the same question.

Everything here is synthetic. `sqlite3` rather than an ORM: one table, no
relations, and the schema fits on a screen. Keeping it stdlib also keeps the
deployment story intact — the whole app is still files on disk.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.config import EMPLOYEE_DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    entity        TEXT NOT NULL,
    location      TEXT NOT NULL,
    level         TEXT NOT NULL,
    department    TEXT NOT NULL,
    worker_type   TEXT NOT NULL,
    tenure_months INTEGER NOT NULL
)
"""

# Tenure *tier* is deliberately absent from the schema. It is a function of
# tenure_months (HR-001 §4.1) and is derived below — storing both would let them
# drift, and the handbook is the authority on where the boundaries sit.
SEED = [
    # Ireland: 25 flat days regardless of tenure, on-call paid as 12% of weekly
    # base, PRSA pension. The single most useful persona for the demo.
    ("jdoe", "John Doe", "Meridian Systems Ireland Ltd.", "Dublin",
     "IC5", "Engineering", "regular full-time", 38),

    # US: PTO by tenure tier, on-call is a USD 500 flat stipend, 401(k).
    # Tier A, so the lowest PTO band — the opposite answer to jdoe.
    ("asmith", "Alex Smith", "Meridian Systems, Inc.", "Austin",
     "M3", "Go-To-Market", "regular full-time", 9),

    # IC7 and Tier C: clears the M4/IC7 threshold for business class, and is
    # the only persona eligible for a sabbatical.
    ("lchen", "Lee Chen", "Meridian Systems APAC Pte. Ltd.", "Singapore",
     "IC7", "Customer Experience", "regular full-time", 74),

    # Germany: 28 flat days, on-call at 6-12% with statutory rest periods.
    # IC6 — one level below business class eligibility, which is the trap.
    ("mgarcia", "Maria Garcia", "Meridian Systems GmbH", "Berlin",
     "IC6", "Engineering", "regular full-time", 44),

    # Contractor: excluded from most of the handbook. No laptop, no benefits,
    # no PTO. Exists to prove the bot notices exclusions rather than answering
    # from the employee tables.
    ("rpatel", "Riley Patel", "Meridian Systems, Inc.", "Remote (US)",
     "n/a", "Engineering", "contractor", 14),
]


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    entity: str
    location: str
    level: str
    department: str
    worker_type: str
    tenure_months: int

    @property
    def tenure_tier(self) -> str:
        """Tier A, B or C per HR-001 §4.1, by completed months of service."""
        if self.tenure_months <= 24:
            return "A"
        if self.tenure_months <= 60:
            return "B"
        return "C"

    def as_context(self) -> str:
        """The profile as the model should read it.

        Written as plain labelled facts rather than a sentence. The model has to
        match these against the handbook's own vocabulary — "Tenure Tier B",
        "Meridian Systems Ireland Ltd." — so the wording deliberately mirrors
        how the documents phrase things.

        The tier is included already resolved. The model could derive it from
        the month count, but that is one more step to get wrong, and HR-001 §4.1
        is the authority either way.
        """
        return (
            f"Employee: {self.name}\n"
            f"Employed by: {self.entity} ({self.location})\n"
            f"Worker type: {self.worker_type}\n"
            f"Job level: {self.level}\n"
            f"Department: {self.department}\n"
            f"Continuous service: {self.tenure_months} completed months "
            f"(Tenure Tier {self.tenure_tier}, HR-001 §4.1)"
        )


def connect(path: Path = EMPLOYEE_DB) -> sqlite3.Connection:
    """Open the database, creating and seeding it on first use."""
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    # Rows come back addressable by column name, so a schema change does not
    # silently shift the meaning of a positional index.
    connection.row_factory = sqlite3.Row
    connection.execute(SCHEMA)

    # INSERT OR IGNORE makes seeding idempotent: safe on every open, and edits
    # to a row survive because a conflicting id is skipped rather than replaced.
    connection.executemany(
        "INSERT OR IGNORE INTO employees "
        "(id, name, entity, location, level, department, worker_type, tenure_months) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        SEED,
    )
    connection.commit()
    return connection


def list_employees() -> list[Employee]:
    """Every profile, for the persona picker."""
    with connect() as connection:
        rows = connection.execute("SELECT * FROM employees ORDER BY name").fetchall()
    return [Employee(**dict(row)) for row in rows]


def get_employee(employee_id: str) -> Employee | None:
    """One profile by id, or None if there is no such employee."""
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
    return Employee(**dict(row)) if row else None