# Data Analysis Helpers

Use these helpers to demonstrate pandas workflows without overwhelming beginners.

- `load_dataset` — load CSV files with optional dtype hints.
- `clean_column_names` — normalize columns to snake_case.
- `summarize_numeric` — compute descriptive stats for numeric columns.
- `fill_missing` — fill missing numeric values via mean, median, or zero.
- `profile_dataframe` — inspect dtypes and missing vs non-missing counts.
- `sample_sales_data` — a tiny, ready-to-use sales dataset for exercises.

Example:
```python
from modules.data_analysis import clean_column_names, fill_missing, load_dataset, summarize_numeric

people = load_dataset("people.csv")
people = clean_column_names(people)
people = fill_missing(people, strategy="median", columns=["age", "income"])
summary = summarize_numeric(people, columns=["age", "income"])
profile = profile_dataframe(people)
print(summary)
print(profile)
```

Quick demo dataset:
```python
from modules.data_analysis import sample_sales_data

sales = sample_sales_data()
print(sales.head())
```
