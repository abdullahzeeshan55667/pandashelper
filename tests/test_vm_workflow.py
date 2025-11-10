from __future__ import annotations

import datetime as dt

import pandas as pd

from pandashelper import PandasShell
import pandashelper.shell as shell_module


def test_vm_compare_creates_expected_datasets(tmp_path, monkeypatch):
    baseline_df = pd.DataFrame(
        {
            "vuln_id": ["A", "B", "C", "D"],
            "cvss_score": [9.5, 7.2, 4.3, 2.0],
            "severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            "category": ["OS", "App", "App", "Network"],
            "age_days": [60, 45, 15, 5],
        }
    )
    current_df = pd.DataFrame(
        {
            "vuln_id": ["B", "C", "E", "F"],
            "cvss_score": [7.2, 4.3, 9.8, 5.5],
            "severity": ["HIGH", "MEDIUM", "CRITICAL", "MEDIUM"],
            "category": ["App", "App", "OS", "Network"],
            "age_days": [38, 20, 3, 12],
        }
    )

    shell = PandasShell()
    baseline_entry = shell.register_dataframe("baseline", baseline_df)
    current_entry = shell.register_dataframe("current", current_df)

    result = shell.vm_compare(baseline_entry, current_entry, key_columns=("vuln_id", "vuln_id"))

    assert result.baseline_total == 4
    assert result.current_total == 4
    assert result.remediated["vuln_id"].tolist() == ["A", "D"]
    assert result.new["vuln_id"].tolist() == ["E", "F"]
    assert result.still_open["vuln_id"].tolist() == ["B", "C"]

    # Summary table contains human readable metrics
    summary_lookup = {row["Metric"]: row for row in result.summary_table.to_dicts()}
    assert summary_lookup["Remediated"]["Value"] == 2
    assert summary_lookup["New This Week"]["Value"] == 2
    assert summary_lookup["Net Change"]["Value"] == 0

    # Severity, age, and category analyses are available
    assert result.severity_breakdown is not None
    current_counts = {row["Severity"]: row["Count"] for row in result.severity_breakdown["current"].to_dicts()}
    assert current_counts["CRITICAL"] == 1
    assert current_counts["HIGH"] == 1

    assert result.age_analysis is not None
    current_age = {row["Age"]: row["Count"] for row in result.age_analysis["current"].to_dicts()}
    assert current_age["31-90"] >= 1

    assert result.category_breakdown is not None
    category_counts = {row["Category"]: row["Count"] for row in result.category_breakdown["current"].to_dicts()}
    assert category_counts["App"] == 2

    # The workflow registers new DataFrames and makes still_open active
    names = [summary.name for summary in shell.list_dataframes()]
    assert names[-3:] == ["remediated_this_week", "new_this_week", "still_open"]
    assert shell.get_active_entry().name == "still_open"

    fixed_timestamp = dt.datetime(2024, 1, 15, 10, 0, 0)

    class _FixedDateTime:
        @classmethod
        def utcnow(cls):
            return fixed_timestamp

    monkeypatch.setattr(shell_module, "datetime", _FixedDateTime)

    exports = shell.export_vm_result(result, tmp_path)
    for path in exports.values():
        assert path.exists()
        assert "20240115" in path.name

    # Exported summary should include metrics for downstream reporting
    summary_export = pd.read_csv(exports["summary"])
    assert "Remediated" in [row["Metric"] for row in summary_export.to_dicts()]
