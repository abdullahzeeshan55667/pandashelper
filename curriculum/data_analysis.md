# Data Analysis Curriculum

## Getting Started with pandas
- **Why**: pandas is the go-to tool for tabular data.
- **Example**:
  ```python
  import pandas as pd

  df = pd.read_csv("people.csv")
  print(df.head())
  ```
- **Checklist**: Can you load CSV data and inspect columns with `info()` and `describe()`?

## Cleaning Data
- **Why**: Real datasets contain missing values and messy labels.
- **Example**:
  ```python
  cleaned = df.dropna(subset=["age"]).assign(name=lambda d: d["name"].str.title())
  ```
- **Checklist**: Can you drop or fill missing values and normalize column names?

## Exploratory Analysis
- **Why**: Descriptive stats guide modeling choices.
- **Example**:
  ```python
  age_summary = df["age"].describe()
  by_city = df.groupby("city")["age"].mean()
  ```
- **Checklist**: Can you compute summaries and group statistics?

## Visualizing Data
- **Why**: Charts reveal patterns quickly.
- **Example**:
  ```python
  import matplotlib.pyplot as plt

  df["age"].hist()
  plt.xlabel("Age")
  plt.ylabel("Count")
  plt.show()
  ```
- **Checklist**: Can you plot basic histograms and line charts with Matplotlib?

## Sharing Insights
- **Why**: Clear communication makes analysis actionable.
- **Example**:
  - Write a 3-bullet summary of findings.
  - Include at least one chart and a table of key metrics.
- **Checklist**: Can you explain what to do next based on the data?
