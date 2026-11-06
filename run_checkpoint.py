"""Run the same 12 expectations against three synthetic weekly extracts."""

from __future__ import annotations

import json
from pathlib import Path

import great_expectations as gx
import pandas as pd

from generate_encounters import AS_OF, write_extracts

ROOT = Path(__file__).resolve().parent
REPORT_PATH = ROOT / "validation_history.json"


def expectation_suite():
    suite = gx.ExpectationSuite(name="encounter_quality")
    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="encounter_id"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="encounter_id"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="mrn"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="event_date"),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="event_date", max_value=pd.Timestamp(AS_OF)
        ),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="zip"),
        gx.expectations.ExpectColumnValuesToMatchRegex(column="zip", regex=r"^\d{5}$"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="age"),
        gx.expectations.ExpectColumnValuesToBeBetween(column="age", min_value=0, max_value=120),
        gx.expectations.ExpectColumnValuesToBeInSet(column="sex", value_set=["Female", "Male"]),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="department"),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="department",
            value_set=["Emergency", "Inpatient", "Outpatient", "Imaging"],
        ),
    ]
    for expectation in expectations:
        suite.add_expectation(expectation)
    return suite


def validate_file(path: Path) -> dict:
    frame = pd.read_csv(path, parse_dates=["event_date"])
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas("encounters")
    asset = source.add_dataframe_asset(name=path.stem)
    batch_definition = asset.add_batch_definition_whole_dataframe("whole")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": frame})
    result = batch.validate(expectation_suite())
    checks = []
    for item in result.results:
        config = item.expectation_config
        checks.append(
            {
                "expectation": config.type,
                "column": config.kwargs.get("column"),
                "success": bool(item.success),
            }
        )
    return {
        "file": path.name,
        "rows": int(len(frame)),
        "expectations": len(checks),
        "passed": sum(1 for check in checks if check["success"]),
        "success_percent": result.statistics["success_percent"],
        "checks": checks,
    }


def main() -> dict:
    history = [validate_file(path) for path in write_extracts()]
    REPORT_PATH.write_text(json.dumps(history, indent=2))
    for item in history:
        print(
            f"{item['file']}: {item['passed']}/{item['expectations']} expectations passed "
            f"({item['success_percent']}% )."
        )
    return {"weeks": history}


if __name__ == "__main__":
    main()
