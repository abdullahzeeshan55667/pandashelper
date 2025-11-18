"""Helper modules for teaching-friendly data analysis.

What we have:
- ``data_analysis`` with CSV loading, column cleaning, missing-value filling, profiling, and a sample sales dataset.

What is missing right now:
- Core dependency ``pandas`` (and optional ``matplotlib``) are not installed in this environment, so examples cannot run yet.
- No integration tests are present; once dependencies are available, add smoke tests around ``sample_sales_data`` and the cleaning/profiling helpers.

Next session idea: after installing dependencies, wire these helpers into the teaching shell demos so learners can explore data immediately.
"""
