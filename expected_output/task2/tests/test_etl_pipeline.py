from expected_output.task2.etl_pipeline import (
    bool_norm,
    norm_project_id,
    norm_ws,
    parse_date,
    parse_money
)


def test_normalize_workspace_id():
    assert norm_ws("ws001") == "WS-001"
    assert norm_ws("ws-001") == "WS-001"
    assert norm_ws("WS-002") == "WS-002"


def test_normalize_project_id():
    assert norm_project_id("prj-1") == "PRJ-001"
    assert norm_project_id("PRJ-001") == "PRJ-001"
    assert norm_project_id("prj001") == "PRJ-001"


def test_bool_normalization():
    assert bool_norm("yes") is True
    assert bool_norm("true") is True
    assert bool_norm(1) is True
    assert bool_norm("false") is False
    assert bool_norm(0) is False


def test_parse_date_to_iso_utc():
    parsed = parse_date("20/02/2024 16:30")
    assert parsed == "2024-02-20T16:30:00Z"

def test_parse_money_converts_eur_values():
    assert parse_money("€12,000") == 12000.0
    assert parse_money("EUR 5000") == 5000.0