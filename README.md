# Pandas Helper Shell

An interactive pandas shell tailored for vulnerability management workflows. The shell ships with utilities for SLA analysis, CVSS severity bucketing, and a week-over-week remediation workflow.

## Installation

```bash
pip install .
```

For development (with tests):

```bash
pip install -e .[test]
```

## Usage

Launch the interactive shell with:

```bash
pandas-shell
```

Type `h` inside the shell to see the list of available commands.

> **Note:** The repository includes a self-contained, minimal pandas implementation that supports the features exercised by the
> shell and unit tests.  No external dependencies are required to run the tool in offline environments.  When a full pandas
> installation is available, the helper now prefers it automatically so you can unlock the richer analytics experience without
> changing any imports.

## Testing

```bash
pytest
```
