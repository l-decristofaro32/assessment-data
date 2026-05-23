#!/usr/bin/env python3
"""Pipeline ETL per l'assessment UNGUESS/Megaditta.

Questo script esegue le seguenti operazioni:
1. Carica i dataset raw da CSV e JSON.
2. Normalizza i campi chiave (es. workspace_id, project_id) in formati canonici.
3. Converte date in formato ISO 8601 UTC.
4. Pulisce e normalizza campi testuali e categorici.
5. Gestisce valori nulli e anomalie nei dati.
6. Esporta i dataset puliti in CSV per l'analisi downstream.
"""

from __future__ import annotations

import json
import logging
import math
import re
import warnings
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
TASK_DIR = ROOT / "expected_output" / "task2"
OUT_DIR = TASK_DIR / "cleaned_data"

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


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Loading raw datasets")

    projects = pd.read_csv(DATA_DIR / "projects_raw.csv")

    interactions = pd.DataFrame(
        json.loads(
            (DATA_DIR / "panelist_interactions.json").read_text(encoding="utf-8")
        )
    )

    return projects, interactions


def transform_projects(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Normalizing project fields")

    df = df.copy()

    df["workspace_id"] = df["workspace_id"].map(norm_ws)
    df["project_id"] = df["project_id"].map(norm_project_id)

    df["start_date"] = df["start_date"].map(parse_date)
    df["end_date"] = df["end_date"].map(parse_date)

    df["budget_eur"] = df["budget"].map(parse_money)

    df["status"] = df["status"].map(normalize_enum)
    df["methodology"] = df["methodology"].map(normalize_methodology)

    if "project_manager" in df.columns:
        df["project_manager"] = df["project_manager"].map(normalize_text)

    return df


def transform_interactions(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Normalizing interaction fields")

    df = df.copy()

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
    if invalid_scores.any():
        logger.warning(
            "Nullified %s satisfaction scores outside range 1-5",
            int(invalid_scores.sum()),
        )
        df.loc[invalid_scores, "satisfaction_score"] = pd.NA

    if "agent_name" in df.columns:
        df["agent_name"] = df["agent_name"].map(normalize_text)

    return df


def run_pipeline() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    projects_raw, interactions_raw = load_raw()

    projects = transform_projects(projects_raw)
    interactions = transform_interactions(interactions_raw)

    projects.to_csv(OUT_DIR / "projects.csv", index=False)
    interactions.to_csv(OUT_DIR / "interactions.csv", index=False)

    logger.info("Field normalization completed")


if __name__ == "__main__":
    run_pipeline()