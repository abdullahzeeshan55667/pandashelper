from __future__ import annotations

import os
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from difflib import SequenceMatcher

import pandas as pd
from pandas import DataFrame
from pandas.api.types import is_numeric_dtype

__all__ = [
    "DataFrameEntry",
    "DataFrameSummary",
    "VMResult",
    "PandasShell",
]


@dataclass
class DataFrameEntry:
    """Container that keeps a loaded DataFrame alongside some metadata."""

    name: str
    dataframe: DataFrame
    created_at: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None


@dataclass
class DataFrameSummary:
    """Represents the output of the ``N`` command."""

    index: int
    name: str
    shape: Tuple[int, int]
    memory_usage: int
    columns_preview: List[str]
    is_active: bool = False

    @property
    def formatted_shape(self) -> str:
        return f"{self.shape[0]} rows × {self.shape[1]} cols"

    @property
    def formatted_memory(self) -> str:
        if self.memory_usage < 1024:
            return f"{self.memory_usage} B"
        if self.memory_usage < 1024 ** 2:
            return f"{self.memory_usage / 1024:.1f} KB"
        if self.memory_usage < 1024 ** 3:
            return f"{self.memory_usage / (1024 ** 2):.1f} MB"
        return f"{self.memory_usage / (1024 ** 3):.1f} GB"


@dataclass
class VMResult:
    """Holds the result of the vulnerability management workflow."""

    baseline_total: int
    current_total: int
    remediated: DataFrame
    new: DataFrame
    still_open: DataFrame
    key_columns: Tuple[str, str]
    summary_table: DataFrame
    severity_breakdown: Optional[Dict[str, DataFrame]] = None
    age_analysis: Optional[Dict[str, DataFrame]] = None
    category_breakdown: Optional[Dict[str, DataFrame]] = None

    @property
    def remediated_count(self) -> int:
        return len(self.remediated)

    @property
    def new_count(self) -> int:
        return len(self.new)

    @property
    def still_open_count(self) -> int:
        return len(self.still_open)

    @property
    def net_change(self) -> int:
        return self.current_total - self.baseline_total

    @property
    def metrics(self) -> Dict[str, int]:
        return {
            "baseline_total": self.baseline_total,
            "current_total": self.current_total,
            "remediated": self.remediated_count,
            "new": self.new_count,
            "still_open": self.still_open_count,
            "net_change": self.net_change,
        }


def normalize_column_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _memory_usage(df: DataFrame) -> int:
    return int(df.memory_usage(deep=True).sum())


SEVERITY_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]


def score_to_severity(value) -> str:
    if pd.isna(value):
        return "UNKNOWN"
    try:
        score = float(value)
    except (TypeError, ValueError):
        return str(value).upper()
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    if score >= 0:
        return "LOW"
    return "UNKNOWN"


SLA_RULES = (
    (900, 7, "CRITICAL Out of Compliance"),
    (700, 30, "HIGH Out of Compliance"),
    (400, 7, "MEDIUM Out of Compliance"),
)


class PandasShell:
    """Implements the core logic behind the interactive shell.

    The public methods in this class are intentionally designed so they can be
    unit-tested without going through the interactive prompt layer.  The
    ``cli`` module is a very small wrapper around these primitives and is not
    required for automated verification.
    """

    def __init__(self) -> None:
        self._registry: List[DataFrameEntry] = []
        self._active_index: Optional[int] = None
        self._history: List[str] = []

    # ------------------------------------------------------------------
    # Registry helpers
    def register_dataframe(self, name: str, dataframe: DataFrame, *, set_active: bool = True, source: Optional[str] = None) -> DataFrameEntry:
        entry_name = self._ensure_unique_name(name)
        entry = DataFrameEntry(name=entry_name, dataframe=dataframe, source=source)
        self._registry.append(entry)
        if set_active:
            self._active_index = len(self._registry) - 1
        return entry

    def _ensure_unique_name(self, base_name: str) -> str:
        existing = {entry.name for entry in self._registry}
        if base_name not in existing:
            return base_name
        suffix = 2
        while f"{base_name}_{suffix}" in existing:
            suffix += 1
        return f"{base_name}_{suffix}"

    def load_dataframe(self, path: str, *, name: Optional[str] = None, **kwargs) -> DataFrameEntry:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if file_path.suffix.lower() in {".xlsx", ".xls"}:
            df = pd.read_excel(file_path, **kwargs)
        else:
            df = pd.read_csv(file_path, **kwargs)
        entry_name = name or file_path.stem
        entry = self.register_dataframe(entry_name, df, source=str(file_path.resolve()))
        self._history.append(f"df_{entry.name} = pd.read_{'excel' if file_path.suffix.lower() in {'.xlsx', '.xls'} else 'csv'}('{path}')")
        return entry

    def list_dataframes(self) -> List[DataFrameSummary]:
        summaries: List[DataFrameSummary] = []
        for index, entry in enumerate(self._registry):
            summaries.append(
                DataFrameSummary(
                    index=index,
                    name=entry.name,
                    shape=entry.dataframe.shape,
                    memory_usage=_memory_usage(entry.dataframe),
                    columns_preview=list(entry.dataframe.columns[:5]),
                    is_active=index == self._active_index,
                )
            )
        return summaries

    def set_active(self, identifier: int | str) -> DataFrameEntry:
        if isinstance(identifier, int):
            index = identifier
        else:
            names = [entry.name for entry in self._registry]
            if identifier not in names:
                raise KeyError(f"Unknown DataFrame '{identifier}'")
            index = names.index(identifier)
        if index < 0 or index >= len(self._registry):
            raise IndexError("DataFrame index out of range")
        self._active_index = index
        return self._registry[index]

    def get_active_entry(self) -> DataFrameEntry:
        if self._active_index is None:
            raise RuntimeError("No active DataFrame. Load data first.")
        return self._registry[self._active_index]

    # ------------------------------------------------------------------
    # Export helpers
    def export_active(self, path: str, *, index: bool = False) -> Path:
        entry = self.get_active_entry()
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        entry.dataframe.to_csv(file_path, index=index)
        self._history.append(f"{entry.name}.to_csv('{path}', index={index})")
        return file_path

    # ------------------------------------------------------------------
    # Column helpers
    def add_today_and_age(
        self,
        date_column: str,
        *,
        today_column: str = "today",
        age_column: Optional[str] = None,
        today_value: Optional[pd.Timestamp] = None,
    ) -> DataFrame:
        entry = self.get_active_entry()
        df = entry.dataframe
        if date_column not in df.columns:
            raise KeyError(f"Column '{date_column}' not found")
        today = (today_value or pd.Timestamp.today()).normalize()
        parsed = pd.to_datetime(df[date_column], errors="coerce")
        ages: List[float] = []
        for value in parsed:
            if value is None:
                ages.append(float("nan"))
            else:
                ages.append(float((today - value).days))
        age_column = age_column or f"{date_column}_age_days"
        df[today_column] = [today for _ in range(len(parsed))]
        df[age_column] = ages
        self._history.append(
            textwrap.dedent(
                f"""
                df['{today_column}'] = pd.Timestamp.today().normalize()
                df['{age_column}'] = (df['{today_column}'] - pd.to_datetime(df['{date_column}'], errors='coerce')).dt.days
                """
            ).strip()
        )
        return df

    def add_cvss_severity(self, score_column: str, *, new_column: str = "cvss_severity") -> DataFrame:
        entry = self.get_active_entry()
        df = entry.dataframe
        if score_column not in df.columns:
            raise KeyError(f"Column '{score_column}' not found")
        df[new_column] = df[score_column].apply(score_to_severity)
        self._history.append(
            f"df['{new_column}'] = df['{score_column}'].apply(score_to_severity)"
        )
        return df

    def add_sla_status(self, risk_column: str, age_column: str, *, new_column: str = "sla_status") -> DataFrame:
        entry = self.get_active_entry()
        df = entry.dataframe
        if risk_column not in df.columns:
            raise KeyError(f"Column '{risk_column}' not found")
        if age_column not in df.columns:
            raise KeyError(f"Column '{age_column}' not found")

        def classify(row) -> str:
            risk = row[risk_column]
            age = row[age_column]
            if pd.isna(risk) or pd.isna(age):
                return "Compliant"
            try:
                risk_value = float(risk)
                age_value = float(age)
            except (TypeError, ValueError):
                return "Compliant"
            for min_risk, min_age, label in SLA_RULES:
                if risk_value >= min_risk and age_value > min_age:
                    return label
            return "Compliant"

        df[new_column] = df.apply(classify, axis=1)
        self._history.append(
            textwrap.dedent(
                f"""
                def _classify_sla(row):
                    risk = float(row['{risk_column}']) if pd.notna(row['{risk_column}']) else None
                    age = float(row['{age_column}']) if pd.notna(row['{age_column}']) else None
                    if risk is None or age is None:
                        return 'Compliant'
                    if risk >= 900 and age > 7:
                        return 'CRITICAL Out of Compliance'
                    if risk >= 700 and age > 30:
                        return 'HIGH Out of Compliance'
                    if risk >= 400 and age > 7:
                        return 'MEDIUM Out of Compliance'
                    return 'Compliant'

                df['{new_column}'] = df.apply(_classify_sla, axis=1)
                """
            ).strip()
        )
        return df

    # ------------------------------------------------------------------
    # Vulnerability management workflow
    def find_identifier_matches(self, baseline_columns: Sequence[str], current_columns: Sequence[str]) -> List[Tuple[str, str, int]]:
        baseline_norm = {col: normalize_column_name(col) for col in baseline_columns}
        current_norm = {col: normalize_column_name(col) for col in current_columns}
        matches: List[Tuple[str, str, int]] = []
        preferred_tokens = {"vulnid", "vulnerabilityid", "cveid", "cve", "findingid", "id"}

        for base_col, base_norm in baseline_norm.items():
            for curr_col, curr_norm in current_norm.items():
                if not base_norm or not curr_norm:
                    continue
                if base_norm == curr_norm:
                    confidence = 100 if base_norm in preferred_tokens else 95
                else:
                    ratio = int(SequenceMatcher(None, base_norm, curr_norm).ratio() * 100)
                    confidence = ratio
                    if base_norm in preferred_tokens or curr_norm in preferred_tokens:
                        confidence = max(confidence, 90)
                if confidence >= 60:
                    matches.append((base_col, curr_col, confidence))
        matches.sort(key=lambda item: item[2], reverse=True)
        return matches

    def _string_identifier_series(self, df: DataFrame, column: str) -> pd.Series:
        series = df[column].fillna("")
        return series.astype(str).str.strip()

    def vm_compare(
        self,
        baseline_entry: DataFrameEntry,
        current_entry: DataFrameEntry,
        *,
        key_columns: Optional[Tuple[str, str]] = None,
        register_results: bool = True,
    ) -> VMResult:
        baseline_df = baseline_entry.dataframe.copy()
        current_df = current_entry.dataframe.copy()
        if key_columns is None:
            matches = self.find_identifier_matches(baseline_df.columns, current_df.columns)
            if not matches:
                raise ValueError("Unable to match identifier columns automatically")
            key_columns = matches[0][:2]
        base_key, curr_key = key_columns
        if base_key not in baseline_df.columns:
            raise KeyError(f"Column '{base_key}' not found in baseline")
        if curr_key not in current_df.columns:
            raise KeyError(f"Column '{curr_key}' not found in current")

        baseline_ids = self._string_identifier_series(baseline_df, base_key)
        current_ids = self._string_identifier_series(current_df, curr_key)
        baseline_df["__vm_identifier__"] = baseline_ids
        current_df["__vm_identifier__"] = current_ids

        baseline_set = set(baseline_ids[baseline_ids != ""])
        current_set = set(current_ids[current_ids != ""])

        remediated_ids = sorted(baseline_set - current_set)
        new_ids = sorted(current_set - baseline_set)
        still_open_ids = sorted(baseline_set & current_set)

        remediated_df = baseline_df[baseline_df["__vm_identifier__"].isin(remediated_ids)].copy()
        new_df = current_df[current_df["__vm_identifier__"].isin(new_ids)].copy()
        still_open_df = current_df[current_df["__vm_identifier__"].isin(still_open_ids)].copy()

        remediated_df["Status"] = "Remediated"
        remediated_df["Change"] = "Closed since last week"
        new_df["Status"] = "New"
        new_df["Change"] = "Discovered this week"
        still_open_df["Status"] = "Open"
        still_open_df["Change"] = "Still open"

        for df in (remediated_df, new_df, still_open_df):
            if "__vm_identifier__" in df.columns:
                df.drop(columns=["__vm_identifier__"], inplace=True)

        baseline_total = len(baseline_df)
        current_total = len(current_df)
        summary_rows = [
            {"Metric": "Last Week Total", "Value": baseline_total},
            {"Metric": "This Week Total", "Value": current_total},
            {
                "Metric": "Remediated",
                "Value": len(remediated_df),
                "Percent of Baseline": self._percentage(len(remediated_df), baseline_total),
            },
            {"Metric": "New This Week", "Value": len(new_df)},
            {
                "Metric": "Still Open",
                "Value": len(still_open_df),
                "Percent of Baseline": self._percentage(len(still_open_df), baseline_total),
            },
            {"Metric": "Net Change", "Value": current_total - baseline_total},
        ]
        summary_table = pd.DataFrame(summary_rows)

        severity_breakdown = self._build_severity_breakdown(current_df, remediated_df, new_df)
        age_analysis = self._build_age_analysis(current_df, remediated_df, new_df)
        category_breakdown = self._build_category_breakdown(current_df, remediated_df, new_df)

        result = VMResult(
            baseline_total=baseline_total,
            current_total=current_total,
            remediated=remediated_df,
            new=new_df,
            still_open=still_open_df,
            key_columns=key_columns,
            summary_table=summary_table,
            severity_breakdown=severity_breakdown,
            age_analysis=age_analysis,
            category_breakdown=category_breakdown,
        )

        if register_results:
            self.register_dataframe("remediated_this_week", remediated_df, set_active=False)
            self.register_dataframe("new_this_week", new_df, set_active=False)
            still_entry = self.register_dataframe("still_open", still_open_df, set_active=True)
            self._history.append(
                textwrap.dedent(
                    f"""
                    # Vulnerability management comparison
                    last_week = df_{baseline_entry.name}
                    this_week = df_{current_entry.name}
                    key = ('{base_key}', '{curr_key}')
                    remediated = last_week[~last_week['{base_key}'].isin(this_week['{curr_key}'])]
                    new = this_week[~this_week['{curr_key}'].isin(last_week['{base_key}'])]
                    still_open = this_week[this_week['{curr_key}'].isin(last_week['{base_key}'])]
                    """
                ).strip()
            )
            # keep active as still open entry
            self._active_index = self._registry.index(still_entry)

        return result

    def export_vm_result(self, result: VMResult, directory: str | os.PathLike[str]) -> Dict[str, Path]:
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        export_dir = Path(directory)
        export_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "remediated": export_dir / f"remediated_{timestamp}.csv",
            "new": export_dir / f"new_vulns_{timestamp}.csv",
            "still_open": export_dir / f"still_open_{timestamp}.csv",
            "summary": export_dir / f"summary_report_{timestamp}.csv",
        }
        result.remediated.to_csv(files["remediated"], index=False)
        result.new.to_csv(files["new"], index=False)
        result.still_open.to_csv(files["still_open"], index=False)
        result.summary_table.to_csv(files["summary"], index=False)
        return files

    # ------------------------------------------------------------------
    # Analysis helpers
    def _percentage(self, numerator: int, denominator: int) -> Optional[float]:
        if denominator == 0:
            return None
        return round((numerator / denominator) * 100, 1)

    def _build_severity_breakdown(
        self,
        current_df: DataFrame,
        remediated_df: DataFrame,
        new_df: DataFrame,
    ) -> Optional[Dict[str, DataFrame]]:
        column = self._detect_severity_column(current_df)
        if column is None:
            return None

        def severity_counts(df: DataFrame) -> DataFrame:
            values = self._coerce_severity(df, column)
            counts = values.value_counts(dropna=False).reindex(SEVERITY_LEVELS, fill_value=0)
            return counts.rename_axis("Severity").reset_index(name="Count")

        return {
            "current": severity_counts(current_df),
            "remediated": severity_counts(remediated_df),
            "new": severity_counts(new_df),
        }

    def _coerce_severity(self, df: DataFrame, column: str) -> pd.Series:
        series = df.get(column)
        if series is None:
            return pd.Series([], dtype=object)
        if is_numeric_dtype(series):
            return series.apply(score_to_severity)
        return series.astype(str).str.upper()

    def _detect_severity_column(self, df: DataFrame) -> Optional[str]:
        candidates: List[str] = []
        for col in df.columns:
            norm = normalize_column_name(col)
            if not norm:
                continue
            if any(token in norm for token in ["severity", "cvss", "risk", "rating"]):
                candidates.append(col)
        if not candidates:
            return None
        # prefer columns that already contain severity labels
        for col in candidates:
            values = df[col].dropna().astype(str).str.upper()
            if any(value in SEVERITY_LEVELS for value in values.unique()):
                return col
        return candidates[0]

    def _build_age_analysis(
        self,
        current_df: DataFrame,
        remediated_df: DataFrame,
        new_df: DataFrame,
    ) -> Optional[Dict[str, DataFrame]]:
        column = self._detect_age_or_date_column(current_df)
        if column is None:
            return None

        def age_bins(df: DataFrame) -> DataFrame:
            series = self._age_series(df, column)
            if series.empty:
                return pd.DataFrame(columns=["Age", "Count"])
            bins = [0, 7, 30, 90, 365, float("inf")]
            labels = ["0-7", "8-30", "31-90", "91-365", "365+"]
            cut = pd.cut(series, bins=bins, labels=labels, right=True)
            counts = cut.value_counts().reindex(labels, fill_value=0)
            return counts.rename_axis("Age").reset_index(name="Count")

        return {
            "current": age_bins(current_df),
            "remediated": age_bins(remediated_df),
            "new": age_bins(new_df),
        }

    def _detect_age_or_date_column(self, df: DataFrame) -> Optional[str]:
        for col in df.columns:
            norm = normalize_column_name(col)
            if "age" in norm:
                return col
        for col in df.columns:
            norm = normalize_column_name(col)
            if any(token in norm for token in ["date", "discover", "found", "opened", "reported"]):
                return col
        return None

    def _age_series(self, df: DataFrame, column: str) -> pd.Series:
        series = df.get(column)
        if series is None:
            return pd.Series([], dtype="float64")
        if series is None:
            return pd.Series([], dtype=float)
        if is_numeric_dtype(series):
            return series.astype(float)
        parsed = pd.to_datetime(series, errors="coerce")
        today = pd.Timestamp.today().normalize()
        ages = []
        for value in parsed:
            if value is None:
                ages.append(float("nan"))
            else:
                ages.append(float((today - value).days))
        return pd.Series(ages, index=parsed.index, dtype=float)

    def _build_category_breakdown(
        self,
        current_df: DataFrame,
        remediated_df: DataFrame,
        new_df: DataFrame,
    ) -> Optional[Dict[str, DataFrame]]:
        column = self._detect_category_column(current_df)
        if column is None:
            return None

        def category_counts(df: DataFrame) -> DataFrame:
            series = df.get(column)
            if series is None:
                return pd.DataFrame(columns=["Category", "Count"])
            counts = series.fillna("Unknown").astype(str).value_counts()
            return counts.rename_axis("Category").reset_index(name="Count")

        return {
            "current": category_counts(current_df),
            "remediated": category_counts(remediated_df),
            "new": category_counts(new_df),
        }

    def _detect_category_column(self, df: DataFrame) -> Optional[str]:
        for col in df.columns:
            norm = normalize_column_name(col)
            if any(token in norm for token in ["category", "type", "group", "family"]):
                return col
        return None

    # ------------------------------------------------------------------
    # Misc helpers
    def history(self) -> List[str]:
        return list(self._history)
