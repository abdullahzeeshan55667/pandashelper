from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

import pandas as pd

from .shell import PandasShell


class ShellCLI:
    """Thin interactive wrapper around :class:`PandasShell`."""

    def __init__(self) -> None:
        self.shell = PandasShell()

    def run(self) -> int:
        print("Pandas Shell v8.0 — type 'h' for help, 'q' to quit")
        while True:
            try:
                command = input("Command: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0

            if not command:
                continue

            command_lower = command.lower()
            if command_lower == "q":
                print("Goodbye!")
                return 0
            if command_lower == "h":
                self._print_help()
                continue
            if command_lower == "l":
                self._handle_load()
                continue
            if command_lower == "n":
                self._handle_memory()
                continue
            if command_lower == "w":
                self._handle_export()
                continue
            if command_lower == "a":
                self._handle_add_column()
                continue
            if command_lower == "vm":
                self._handle_vm()
                continue
            if command_lower == "y":
                self._handle_history()
                continue

            print("Unknown command. Type 'h' for help.")

    # ------------------------------------------------------------------
    # Command implementations
    def _handle_load(self) -> None:
        path = input("File path: ").strip()
        if not path:
            print("No file provided.")
            return
        try:
            entry = self.shell.load_dataframe(path)
        except FileNotFoundError:
            print(f"File not found: {path}")
            return
        except pd.errors.EmptyDataError:
            print("File is empty or invalid.")
            return
        print(f"✓ Loaded '{entry.name}' with shape {entry.dataframe.shape[0]} × {entry.dataframe.shape[1]}")

    def _handle_memory(self) -> None:
        summaries = self.shell.list_dataframes()
        if not summaries:
            print("No DataFrames in memory. Load data with 'L'.")
            return
        print("Loaded DataFrames:")
        for summary in summaries:
            star = "⭐" if summary.is_active else " "
            columns = ", ".join(summary.columns_preview)
            print(
                f"  [{summary.index}] {summary.name} {star}\n"
                f"      Shape: {summary.formatted_shape}\n"
                f"      Memory: {summary.formatted_memory}\n"
                f"      Columns: {columns}"
            )
        selection = input("Switch to DataFrame [index], view [v+index], or Enter to return: ").strip()
        if not selection:
            return
        if selection.startswith("v"):
            try:
                index = int(selection[1:])
            except ValueError:
                print("Invalid selection.")
                return
            try:
                entry = self.shell.set_active(index)
            except (IndexError, KeyError) as exc:
                print(str(exc))
                return
            print(entry.dataframe)
            return
        try:
            index = int(selection)
        except ValueError:
            print("Invalid selection.")
            return
        try:
            entry = self.shell.set_active(index)
        except (IndexError, KeyError) as exc:
            print(str(exc))
            return
        print(f"Active DataFrame set to '{entry.name}'")

    def _handle_export(self) -> None:
        try:
            self.shell.get_active_entry()
        except RuntimeError:
            print("No active DataFrame. Load data first.")
            return
        path = input("Output CSV path: ").strip()
        if not path:
            print("No path provided.")
            return
        file_path = self.shell.export_active(path)
        print(f"✓ Exported to {file_path}")

    def _handle_add_column(self) -> None:
        try:
            entry = self.shell.get_active_entry()
        except RuntimeError:
            print("No active DataFrame. Load data first.")
            return
        print("Add column options:")
        print("  [2] Today + Age")
        print("  [3] CVSS Severity Buckets")
        print("  [4] SLA Compliance Status")
        choice = input("Choice: ").strip()
        if choice == "2":
            date_column = self._prompt_column(entry, "Date column for age calculation")
            if not date_column:
                return
            today_col = input("Today column name [today]: ").strip() or "today"
            age_col = input("Age column name [auto]: ").strip() or None
            self.shell.add_today_and_age(date_column, today_column=today_col, age_column=age_col)
            print("✓ Added today and age columns.")
        elif choice == "3":
            score_column = self._prompt_column(entry, "CVSS score column")
            if not score_column:
                return
            column_name = input("Severity column name [cvss_severity]: ").strip() or "cvss_severity"
            self.shell.add_cvss_severity(score_column, new_column=column_name)
            print("✓ Added CVSS severity buckets.")
        elif choice == "4":
            risk_column = self._prompt_column(entry, "Risk/Score column")
            if not risk_column:
                return
            age_column = self._prompt_column(entry, "Age (days) column")
            if not age_column:
                return
            status_column = input("SLA status column name [sla_status]: ").strip() or "sla_status"
            self.shell.add_sla_status(risk_column, age_column, new_column=status_column)
            print("✓ Added SLA status column.")
        else:
            print("Invalid choice.")

    def _prompt_column(self, entry, message: str) -> Optional[str]:
        print(message + ":")
        for idx, column in enumerate(entry.dataframe.columns):
            print(f"  [{idx}] {column}")
        selection = input("Column name or index: ").strip()
        if not selection:
            print("No column selected.")
            return None
        if selection.isdigit():
            index = int(selection)
            if index < 0 or index >= len(entry.dataframe.columns):
                print("Invalid index.")
                return None
            return entry.dataframe.columns[index]
        if selection not in entry.dataframe.columns:
            print("Column not found.")
            return None
        return selection

    def _handle_vm(self) -> None:
        print("\n" + "═" * 63)
        print("STEP 1: Select LAST WEEK's data (baseline)")
        print("" + "═" * 63)
        baseline_path = input("Last week file: ").strip()
        if not baseline_path:
            print("No file selected.")
            return
        try:
            baseline_entry = self.shell.load_dataframe(baseline_path, name="baseline")
        except Exception as exc:
            print(f"Failed to load baseline: {exc}")
            return
        print(f"\n✓ Loaded baseline: {len(baseline_entry.dataframe)} vulnerabilities")

        print("\n" + "═" * 63)
        print("STEP 2: Select THIS WEEK's data (current)")
        print("" + "═" * 63)
        current_path = input("This week file: ").strip()
        if not current_path:
            print("No file selected.")
            return
        try:
            current_entry = self.shell.load_dataframe(current_path, name="current")
        except Exception as exc:
            print(f"Failed to load current data: {exc}")
            return
        print(f"\n✓ Loaded current: {len(current_entry.dataframe)} vulnerabilities")

        print("\n" + "═" * 63)
        print("STEP 3: Identify vulnerability identifier column")
        print("" + "═" * 63)
        matches = self.shell.find_identifier_matches(
            baseline_entry.dataframe.columns, current_entry.dataframe.columns
        )
        if not matches:
            print("Could not determine matching columns.")
            return
        print("\nFound potential matches:")
        for idx, (base_col, curr_col, confidence) in enumerate(matches[:5]):
            print(f"  [{idx}] {base_col} ↔ {curr_col} (confidence: {confidence}%)")
        use_suggested = input("Use suggested match? [Y/n]: ").strip().lower()
        if use_suggested in {"", "y", "yes"}:
            match_index = 0
        else:
            try:
                match_index = int(input("Match index: ").strip())
            except ValueError:
                print("Invalid selection.")
                return
        try:
            selected = matches[match_index]
        except IndexError:
            print("Invalid match selection.")
            return
        base_col, curr_col, _ = selected
        print(f"\n✓ Using keys: '{base_col}' ↔ '{curr_col}'\n")

        result = self.shell.vm_compare(baseline_entry, current_entry, key_columns=(base_col, curr_col))

        print("" + "═" * 63)
        print("STEP 4: Analyzing changes...")
        print("" + "═" * 63)
        print("\n📊 REMEDIATION METRICS")
        print("-" * 64)
        print(f"Last Week Total: {result.baseline_total:>12} vulnerabilities")
        print(f"This Week Total: {result.current_total:>12} vulnerabilities")
        percent_remediated = self._lookup_metric(result.summary_table, "Remediated", "Percent of Baseline")
        percent_open = self._lookup_metric(result.summary_table, "Still Open", "Percent of Baseline")
        print(
            f"\n✅ Remediated: {result.remediated_count:>14} ({percent_remediated if percent_remediated is not None else 'N/A'}% of baseline)"
        )
        print(f"🆕 New This Week: {result.new_count:>11}")
        print(
            f"⚠️  Still Open: {result.still_open_count:>12} ({percent_open if percent_open is not None else 'N/A'}% of baseline)"
        )
        print(f"\n📉 Net Change: {result.net_change:+d}\n")

        if result.severity_breakdown:
            print("Severity breakdown available (option 1 in additional analysis).")
        if result.age_analysis:
            print("Age analysis available (option 2 in additional analysis).")
        if result.category_breakdown:
            print("Category breakdown available (option 3 in additional analysis).")

        self._additional_analysis_menu(result)

    def _additional_analysis_menu(self, result) -> None:
        while True:
            print("\n" + "═" * 63)
            print("ADDITIONAL ANALYSIS")
            print("" + "═" * 63)
            print("  [1] Severity breakdown")
            print("  [2] Age analysis")
            print("  [3] Category breakdown")
            print("  [4] Export all trend data")
            print("  [5] Return to main menu")
            choice = input("Choice: ").strip()
            if choice == "1" and result.severity_breakdown:
                self._print_named_dataframe("Severity — This Week", result.severity_breakdown["current"])
                self._print_named_dataframe("Severity — Remediated", result.severity_breakdown["remediated"])
                self._print_named_dataframe("Severity — New", result.severity_breakdown["new"])
            elif choice == "2" and result.age_analysis:
                self._print_named_dataframe("Age — This Week", result.age_analysis["current"])
                self._print_named_dataframe("Age — Remediated", result.age_analysis["remediated"])
                self._print_named_dataframe("Age — New", result.age_analysis["new"])
            elif choice == "3" and result.category_breakdown:
                self._print_named_dataframe("Category — This Week", result.category_breakdown["current"])
                self._print_named_dataframe("Category — Remediated", result.category_breakdown["remediated"])
                self._print_named_dataframe("Category — New", result.category_breakdown["new"])
            elif choice == "4":
                directory = input("Export directory [exports]: ").strip() or "exports"
                files = self.shell.export_vm_result(result, directory)
                for label, path in files.items():
                    print(f"✓ Exported {label} → {path}")
            elif choice == "5" or not choice:
                return
            else:
                print("Option not available.")

    def _print_named_dataframe(self, title: str, df: pd.DataFrame) -> None:
        print(f"\n{title}")
        print(df.to_string(index=False))

    def _handle_history(self) -> None:
        history = self.shell.history()
        if not history:
            print("No history yet.")
            return
        print("Generated pandas code:")
        for line in history:
            print(line)

    def _print_help(self) -> None:
        print(
            """\
Commands:
  L  Load data file
  N  View DataFrames in memory
  A  Add derived columns (today/age, CVSS severity, SLA)
  VM Vulnerability week-over-week workflow
  W  Export active DataFrame to CSV
  Y  Show pandas history
  H  Help
  Q  Quit
"""
        )

    def _lookup_metric(self, table: pd.DataFrame, metric: str, column: str) -> Optional[float]:
        for row in table.to_dicts():
            if row.get("Metric") == metric:
                return row.get(column)
        return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Interactive pandas helper shell")
    parser.add_argument("--version", action="store_true", help="Print version information and exit")
    args = parser.parse_args(argv)
    if args.version:
        print("Pandas Shell v8.0")
        return 0
    cli = ShellCLI()
    return cli.run()


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    sys.exit(main())
