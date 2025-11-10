import math

import pandas as pd

from pandashelper import PandasShell


def _create_shell_with_dataframe(df: pd.DataFrame) -> PandasShell:
    shell = PandasShell()
    shell.register_dataframe("data", df.copy())
    return shell


def test_add_today_and_age_creates_columns():
    df = pd.DataFrame({"discovered": ["2024-01-01", "2024-01-10", None]})
    shell = _create_shell_with_dataframe(df)
    today = pd.Timestamp("2024-01-11")

    shell.add_today_and_age("discovered", today_value=today)
    entry = shell.get_active_entry()
    result_df = entry.dataframe

    assert "today" in result_df.columns
    assert "discovered_age_days" in result_df.columns
    assert all(result_df["today"] == today.normalize())
    ages = result_df["discovered_age_days"].tolist()
    assert ages[0] == 10
    assert ages[1] == 1
    assert math.isnan(ages[2])


def test_add_cvss_severity_buckets():
    df = pd.DataFrame({"cvss": [9.5, 7.2, 4.5, 3.5, None, "High"]})
    shell = _create_shell_with_dataframe(df)

    shell.add_cvss_severity("cvss", new_column="severity")
    entry = shell.get_active_entry()
    result = entry.dataframe["severity"].tolist()

    assert result == [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
        "UNKNOWN",
        "HIGH",
    ]


def test_add_sla_status_applies_rules():
    df = pd.DataFrame(
        {
            "risk": [950, 750, 650, 500, 200],
            "age_days": [8, 40, 10, 3, 50],
        }
    )
    shell = _create_shell_with_dataframe(df)

    shell.add_sla_status("risk", "age_days", new_column="sla")
    result = shell.get_active_entry().dataframe["sla"].tolist()

    assert result == [
        "CRITICAL Out of Compliance",
        "HIGH Out of Compliance",
        "MEDIUM Out of Compliance",
        "Compliant",
        "Compliant",
    ]
