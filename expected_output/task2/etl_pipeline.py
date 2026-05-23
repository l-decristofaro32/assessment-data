#!/usr/bin/env python3
"""Pipeline ETL per l'assessment UNGUESS/Megaditta.

Esegue:
1. Caricamento dataset raw.
2. Normalizzazione campi chiave.
3. Deduplica con strategia "record più completo vince".
4. Pseudonimizzazione PII.
5. Validazione leggera con Pandera, se disponibile.
6. Export dataset puliti e report data quality.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import pandera.pandas as pa
    from pandera.pandas import Check, Column, DataFrameSchema
except Exception:
    pa = None
    Check = Column = DataFrameSchema = None


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
TASK_DIR = ROOT / "expected_output" / "task2"
OUT_DIR = TASK_DIR / "cleaned_data"
REPORT_PATH = TASK_DIR / "data_quality_report.md"

NULL_TOKENS = {"", "N/A", "NA", "NULL", "NONE", "NAN"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("etl")


def norm_null(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None

    text = str(value).strip()
    return None if text.upper() in NULL_TOKENS else text


def norm_ws(value: Any) -> str | None:
    value = norm_null(value)
    if not value:
        return None

    match = re.match(r"WS-?0*(\d+)$", value.upper())
    return f"WS-{int(match.group(1)):03d}" if match else value.upper()


def norm_project_id(value: Any) -> str | None:
    value = norm_null(value)
    if not value:
        return None

    match = re.match(r"PRJ-?0*(\d+)$", value.upper().replace(" ", ""))
    return f"PRJ-{int(match.group(1)):03d}" if match else value.upper()


def parse_date(value: Any) -> str | None:
    value = norm_null(value)
    if not value:
        return None

    for dayfirst in (True, False):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(value, errors="coerce", dayfirst=dayfirst, utc=True)

        if pd.notna(parsed):
            return parsed.isoformat().replace("+00:00", "Z")

    logger.warning("Unable to parse date: %r", value)
    return None


def parse_money(value: Any) -> float | None:
    value = norm_null(value)
    if not value:
        return None

    cleaned = (
        str(value)
        .replace("€", "")
        .replace("EUR", "")
        .replace(",", "")
        .strip()
    )

    try:
        amount = float(cleaned)
        return amount if amount >= 0 else None
    except ValueError:
        logger.warning("Unable to parse budget: %r", value)
        return None


def bool_norm(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)) and not pd.isna(value):
        return bool(int(value))

    return {
        "true": True,
        "1": True,
        "yes": True,
        "y": True,
        "false": False,
        "0": False,
        "no": False,
        "n": False,
    }.get(str(value).strip().lower())


def normalize_text(value: Any) -> str | None:
    value = norm_null(value)
    if not value:
        return None

    return re.sub(r"\s+", " ", value).strip()


def normalize_enum(value: Any) -> str | None:
    value = normalize_text(value)
    if not value:
        return None

    return value.title()


def normalize_methodology(value: Any) -> str | None:
    value = normalize_text(value)
    if not value:
        return None

    mapping = {
        "online survey": "CAWI",
        "online panel": "CAWI",
        "cawi": "CAWI",
        "telephone survey": "CATI",
        "cati": "CATI",
        "mixed": "Mixed Methods",
        "mixed methods": "Mixed Methods",
        "focus group": "Focus Group",
        "in-depth interview": "In-depth Interview",
        "idi": "In-depth Interview",
    }

    return mapping.get(value.lower(), value.title())


def hash_value(value: Any) -> str | None:
    value = norm_null(value)
    if not value:
        return None

    return hashlib.sha256(value.lower().encode("utf-8")).hexdigest()[:16]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Loading raw datasets")

    projects = pd.read_csv(DATA_DIR / "projects_raw.csv")

    interactions = pd.DataFrame(
        json.loads(
            (DATA_DIR / "panelist_interactions.json").read_text(encoding="utf-8")
        )
    )

    return projects, interactions


def transform_projects(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    logger.info("Normalizing project fields")

    df = df.copy()
    stats = {"raw_projects": len(df)}

    df["workspace_id"] = df["workspace_id"].map(norm_ws)
    df["project_id"] = df["project_id"].map(norm_project_id)

    df["start_date"] = df["start_date"].map(parse_date)
    df["end_date"] = df["end_date"].map(parse_date)

    start_dt = pd.to_datetime(df["start_date"], errors="coerce", utc=True)
    end_dt = pd.to_datetime(df["end_date"], errors="coerce", utc=True)

    invalid_date_ranges = (
        start_dt.notna()
        & end_dt.notna()
        & (end_dt < start_dt)
    )

    stats["invalid_project_date_ranges"] = int(invalid_date_ranges.sum())

    if invalid_date_ranges.any():
        logger.warning(
            "Found %s project records with end_date before start_date",
            stats["invalid_project_date_ranges"],
        )

    df["budget_eur"] = df["budget"].map(parse_money)

    df["status"] = df["status"].map(normalize_enum)
    df["methodology"] = df["methodology"].map(normalize_methodology)

    if "project_manager" in df.columns:
        df["project_manager"] = df["project_manager"].map(normalize_text)

    before = len(df)

    df["_completeness"] = df.notna().sum(axis=1)

    df = (
        df.sort_values(
            ["workspace_id", "project_id", "_completeness"],
            ascending=[True, True, False],
        )
        .drop_duplicates(["workspace_id", "project_id"])
        .drop(columns=["_completeness"])
        .reset_index(drop=True)
    )

    stats["canonical_projects"] = len(df)
    stats["project_duplicates_removed"] = before - len(df)

    logger.info("Removed %s duplicate project records", stats["project_duplicates_removed"])

    return df, stats


def transform_interactions(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    logger.info("Normalizing interactions and pseudonymizing PII")

    df = df.copy()
    stats = {"raw_interactions": len(df)}

    df["workspace_id"] = df["workspace_id"].map(norm_ws)
    df["project_id"] = df["project_ref"].map(norm_project_id)

    df["panelist_id"] = df["panelist_id"].astype(str).str.strip()
    df["interaction_date"] = df["interaction_date"].map(parse_date)

    df["channel"] = df["channel"].map(normalize_enum)
    df["issue_type"] = df["issue_type"].map(normalize_enum)

    df["resolved"] = df["resolved"].map(bool_norm)

    df["resolution_time_hours"] = pd.to_numeric(
        df["resolution_time_hours"],
        errors="coerce",
    )

    df["satisfaction_score"] = pd.to_numeric(
        df["satisfaction_score"],
        errors="coerce",
    )

    invalid_scores = (
        df["satisfaction_score"].notna()
        & ~df["satisfaction_score"].between(1, 5)
    )

    stats["invalid_satisfaction_scores"] = int(invalid_scores.sum())

    if invalid_scores.any():
        logger.warning(
            "Nullified %s satisfaction scores outside range 1-5",
            int(invalid_scores.sum()),
        )
        df.loc[invalid_scores, "satisfaction_score"] = pd.NA

    if "agent_name" in df.columns:
        df["agent_name"] = df["agent_name"].map(normalize_text)

    df["panelist_email_hash"] = df["panelist_email"].map(hash_value)
    df["panelist_phone_hash"] = df["panelist_phone"].map(hash_value)

    df = df.drop(columns=["panelist_email", "panelist_phone"])

    before = len(df)

    df = df.drop_duplicates(["interaction_id"]).reset_index(drop=True)

    stats["canonical_interactions"] = len(df)
    stats["interaction_duplicates_removed"] = before - len(df)

    panelists = (
        df[
            [
                "workspace_id",
                "panelist_id",
                "panelist_email_hash",
                "panelist_phone_hash",
            ]
        ]
        .drop_duplicates(["workspace_id", "panelist_id"])
        .reset_index(drop=True)
    )

    agents = (
        df[["workspace_id", "agent_name"]]
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )

    logger.info(
        "Removed %s duplicate interaction records",
        stats["interaction_duplicates_removed"],
    )

    return df, panelists, agents, stats


def validate_outputs(projects: pd.DataFrame, interactions: pd.DataFrame) -> list[str]:
    """Validation leggera. Pandera è opzionale per non rendere fragile l'assessment."""

    if pa is None:
        logger.warning("Pandera not installed: skipping schema validation")
        return []

    logger.info("Running lightweight Pandera validation")

    issues: list[str] = []

    project_schema = DataFrameSchema(
        {
            "workspace_id": Column(str, Check.str_matches(r"^WS-\d{3}$")),
            "project_id": Column(str, Check.str_matches(r"^PRJ-\d{3}$")),
            "budget_eur": Column(float, Check.ge(0), nullable=True, coerce=True),
        },
        strict=False,
    )

    interaction_schema = DataFrameSchema(
        {
            "workspace_id": Column(str, Check.str_matches(r"^WS-\d{3}$")),
            "interaction_id": Column(str, unique=True),
            "satisfaction_score": Column(
                float,
                Check.in_range(1, 5),
                nullable=True,
                coerce=True,
            ),
        },
        strict=False,
    )

    try:
        project_schema.validate(projects, lazy=True)
    except pa.errors.SchemaErrors as exc:
        logger.warning("Project validation failures:\n%s", exc.failure_cases)
        issues.append(f"projects: {len(exc.failure_cases)} validation failures")

    try:
        interaction_schema.validate(interactions, lazy=True)
    except pa.errors.SchemaErrors as exc:
        issues.append(f"interactions: {len(exc.failure_cases)} validation failures")

    return issues

def write_quality_report(
    stats: dict[str, int],
    validation_issues: list[str],
) -> None:
    logger.info("Writing data quality report")

    lines = [
        "# Data Quality Report",
        "",
        "## Summary",
        "",
        f"- Raw project records: {stats['raw_projects']}",
        f"- Canonical project records: {stats['canonical_projects']}",
        f"- Project duplicates removed: {stats['project_duplicates_removed']}",
        f"- Raw interaction records: {stats['raw_interactions']}",
        f"- Canonical interaction records: {stats['canonical_interactions']}",
        f"- Interaction duplicates removed: {stats['interaction_duplicates_removed']}",
        f"- Invalid satisfaction scores nullified: {stats['invalid_satisfaction_scores']}",
        "",
        "## Validation",
        "",
        "- Logging: standard Python logging to console.",
        "- Pandera: lightweight, non-blocking schema checks for key fields when installed.",
        "- Unit tests: focused tests for normalization helpers.",
        "",
    ]

    if validation_issues:
        lines.extend(f"- {issue}" for issue in validation_issues)
    else:
        lines.append("No blocking validation issues found.")

    lines.extend(
        [
            "",
            "## Main issues found",
            "",
            "- Mixed date formats across CSV and JSON records.",
            "- Inconsistent casing/formatting for `workspace_id`, `project_ref`, `channel`, and methodology values.",
            "- Null-like values represented as empty strings, `N/A`, `null`, and `0`.",
            "- PII in support interactions: email and phone were pseudonymized and removed from cleaned interaction records.",
            "- Mixed boolean representations such as `true`, `yes`, `1`, and `TRUE`.",
            "- Out-of-range satisfaction scores were converted to null instead of guessed.",
            "",
            "## Decisions",
            "",
            "- `workspace_id` and `project_id` are canonicalized to `WS-001` and `PRJ-001` formats.",
            "- Dates are normalized to UTC ISO 8601 where parsable.",
            "- Duplicate projects are resolved by keeping the most complete record for each `(workspace_id, project_id)`.",
            "- Raw PII is not included in the cleaned interaction table; deterministic hashes are kept for entity linkage.",
            "",
            "## Production next steps",
            "",
            "For production I would move these checks into CI, persist rejected records to a quarantine table, "
            "and expose data-quality metrics/alerts in CloudWatch or a similar monitoring system.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

def run_pipeline() -> dict[str, int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    projects_raw, interactions_raw = load_raw()

    projects, project_stats = transform_projects(projects_raw)

    interactions, panelists, agents, interaction_stats = transform_interactions(
        interactions_raw
    )

    validation_issues = validate_outputs(projects, interactions)

    stats = {
        **project_stats,
        **interaction_stats,
        "validation_issues": len(validation_issues),
    }

    write_quality_report(stats, validation_issues)

    projects.to_csv(OUT_DIR / "projects.csv", index=False)
    interactions.to_csv(OUT_DIR / "interactions.csv", index=False)
    panelists.to_csv(OUT_DIR / "panelists.csv", index=False)
    agents.to_csv(OUT_DIR / "agents.csv", index=False)

    projects[["methodology"]].dropna().drop_duplicates().rename(
        columns={"methodology": "methodology_name"}
    ).to_csv(
        OUT_DIR / "methodologies.csv",
        index=False,
    )

    logger.info("ETL completed")

    return stats


if __name__ == "__main__":
    run_pipeline()