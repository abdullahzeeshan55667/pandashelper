"""Reusable data analysis helpers for teaching examples.

These functions avoid external dependencies beyond pandas and matplotlib, and keep
parameters explicit so beginners can see what is happening.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def load_dataset(csv_path: str | Path, *, dtype: dict | None = None) -> pd.DataFrame:
    """Load a CSV file with explicit dtypes.

    Parameters
    ----------
    csv_path:
        Path to the CSV file.
    dtype:
        Optional mapping of column names to dtypes.
    """
    return pd.read_csv(csv_path, dtype=dtype)


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with snake_case column names."""
    renamed = {col: col.strip().lower().replace(" ", "_") for col in df.columns}
    return df.rename(columns=renamed)


def summarize_numeric(df: pd.DataFrame, columns: Iterable[str] | None = None) -> pd.DataFrame:
    """Compute descriptive statistics for numeric columns.

    Parameters
    ----------
    df:
        The DataFrame to summarize.
    columns:
        A subset of numeric columns to summarize. If ``None``, all numeric columns are used.
    """
    subset = df if columns is None else df[list(columns)]
    return subset.describe().T


def fill_missing(df: pd.DataFrame, strategy: str = "mean", *, columns: Iterable[str] | None = None) -> pd.DataFrame:
    """Fill missing numeric values using a simple strategy.

    Strategies supported:
    - ``"mean"`` (default)
    - ``"median"``
    - ``"zero"``
    """
    subset = df[list(columns)] if columns else df
    filled = subset.copy()

    for col in filled.select_dtypes(include="number"):
        if strategy == "mean":
            filled[col] = filled[col].fillna(filled[col].mean())
        elif strategy == "median":
            filled[col] = filled[col].fillna(filled[col].median())
        elif strategy == "zero":
            filled[col] = filled[col].fillna(0)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

    if columns:
        df = df.copy()
        df[columns] = filled
        return df

    return filled


def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a quick profile with dtypes and missing-value counts.

    This is intentionally light so beginners can see column health at a glance.
    """

    profile = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "non_missing": df.notna().sum(),
    })
    return profile


def sample_sales_data() -> pd.DataFrame:
    """Provide a tiny sales dataset for instant analysis demos."""

    return pd.DataFrame(
        {
            "region": ["north", "north", "south", "south", "west", "west"],
            "sales": [1200, 1500, 900, 1100, 1600, 1700],
            "units": [30, 42, 24, 27, 50, 55],
            "category": ["hardware", "software", "hardware", "services", "software", "services"],
        }
    )
