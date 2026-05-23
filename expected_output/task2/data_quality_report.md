# Data Quality Report

## Summary

- Raw project records: 54
- Canonical project records: 50
- Project duplicates removed: 4
- Raw interaction records: 37
- Canonical interaction records: 37
- Interaction duplicates removed: 0
- Invalid satisfaction scores nullified: 1
- Project validation issues: 1 record has missing `workspace_id` after normalization.

## Validation

- Logging: standard Python logging to console.
- Pandera: lightweight, non-blocking schema checks for key fields when installed.
- Unit tests: focused tests for normalization helpers.

- projects: 1 validation failures

## Main issues found

- Mixed date formats across CSV and JSON records.
- Inconsistent casing/formatting for `workspace_id`, `project_ref`, `channel`, and methodology values.
- Null-like values represented as empty strings, `N/A`, `null`, and `0`.
- PII in support interactions: email and phone were pseudonymized and removed from cleaned interaction records.
- Mixed boolean representations such as `true`, `yes`, `1`, and `TRUE`.
- Out-of-range satisfaction scores were converted to null instead of guessed.
- One project record has missing `workspace_id`; it was retained but flagged by validation.

## Decisions

- `workspace_id` and `project_id` are canonicalized to `WS-001` and `PRJ-001` formats.
- Dates are normalized to UTC ISO 8601 where parsable.
- Duplicate projects are resolved by keeping the most complete record for each `(workspace_id, project_id)`.
- Raw PII is not included in the cleaned interaction table; deterministic hashes are kept for entity linkage.

## Production next steps

For production I would move these checks into CI, persist rejected records to a quarantine table, and expose data-quality metrics/alerts in CloudWatch or a similar monitoring system.