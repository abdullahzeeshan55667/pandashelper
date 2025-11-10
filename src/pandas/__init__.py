from __future__ import annotations

import csv
import datetime as _dt
import math
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Sequence

__all__ = [
    "DataFrame",
    "Series",
    "Timestamp",
    "to_datetime",
    "cut",
    "read_csv",
    "read_excel",
    "errors",
    "isna",
]


class EmptyDataError(ValueError):
    pass


class _ErrorsModule:
    EmptyDataError = EmptyDataError


def _is_na(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


errors = _ErrorsModule()


def isna(value: Any) -> bool:
    return _is_na(value)


def _coerce_timestamp(value: Any, *, errors: str = "raise") -> Optional["Timestamp"]:
    if isinstance(value, Timestamp):
        return value
    if isinstance(value, _dt.datetime):
        return Timestamp.fromdatetime(value)
    if isinstance(value, _dt.date):
        return Timestamp(value.year, value.month, value.day)
    if value is None or value == "":
        if errors == "coerce":
            return None
        raise ValueError("Cannot parse datetime")
    text = str(value)
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            dt_value = _dt.datetime.strptime(text, fmt)
            return Timestamp.fromdatetime(dt_value)
        except ValueError:
            continue
    try:
        return Timestamp.fromdatetime(_dt.datetime.fromisoformat(text))
    except ValueError:
        if errors == "coerce":
            return None
        raise ValueError(f"Cannot parse datetime: {value}")


class Timestamp(_dt.datetime):
    def __new__(cls, *args: Any, **kwargs: Any) -> "Timestamp":
        if len(args) == 1 and not kwargs:
            parsed = _coerce_timestamp(args[0])
            if parsed is None:
                raise ValueError("Cannot construct Timestamp from None")
            return _dt.datetime.__new__(cls, parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second, parsed.microsecond)
        return _dt.datetime.__new__(cls, *args, **kwargs)
    @classmethod
    def today(cls) -> "Timestamp":
        now = _dt.datetime.today()
        return cls(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)

    @classmethod
    def utcnow(cls) -> "Timestamp":
        now = _dt.datetime.utcnow()
        return cls(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)

    @classmethod
    def fromdatetime(cls, value: _dt.datetime) -> "Timestamp":
        return cls(value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond)

    def normalize(self) -> "Timestamp":
        return Timestamp(self.year, self.month, self.day)


class Series:
    def __init__(self, data: Optional[Iterable[Any]] = None, *, index: Optional[Sequence[Any]] = None, name: Optional[str] = None, dtype: Any = None) -> None:
        values = list(data) if data is not None else []
        if index is None:
            index = list(range(len(values)))
        if len(index) != len(values):
            raise ValueError("Index length must match data length")
        self._data = values
        self.index = list(index)
        self.name = name
        self.dtype = dtype
        self._axis_name: Optional[str] = None

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._data)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Series({self._data})"

    def __eq__(self, other: Any) -> "Series":
        if isinstance(other, self.__class__):
            if len(other) != len(self):
                raise ValueError("Series must be same length for comparison")
            data = [a == b for a, b in zip(self._data, other._data)]
            return Series(data, index=self.index)
        return Series([value == other for value in self._data], index=self.index)

    def __ne__(self, other: Any) -> "Series":
        equality = self.__eq__(other)
        return Series([not bool(value) for value in equality], index=equality.index)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return self._data[key]
        if isinstance(key, slice):
            return Series(self._data[key], index=self.index[key], name=self.name)
        if isinstance(key, self.__class__):
            mask = [bool(item) for item in key]
            data = [value for value, keep in zip(self._data, mask) if keep]
            idx = [index for index, keep in zip(self.index, mask) if keep]
            return Series(data, index=idx, name=self.name)
        if isinstance(key, list):
            if key and isinstance(key[0], bool):
                mask = [bool(item) for item in key]
                data = [value for value, keep in zip(self._data, mask) if keep]
                idx = [index for index, keep in zip(self.index, mask) if keep]
                return Series(data, index=idx, name=self.name)
            data = [self._data[idx] for idx in key]
            idx = [self.index[idx] for idx in key]
            return Series(data, index=idx, name=self.name)
        raise TypeError("Unsupported indexer for Series")

    def copy(self) -> "Series":
        return Series(self._data.copy(), index=self.index.copy(), name=self.name, dtype=self.dtype)

    @property
    def empty(self) -> bool:
        return len(self._data) == 0

    def tolist(self) -> List[Any]:
        return self._data.copy()

    def fillna(self, value: Any) -> "Series":
        return Series([value if _is_na(item) else item for item in self._data], index=self.index, name=self.name)

    def dropna(self) -> "Series":
        filtered = [(idx, item) for idx, item in zip(self.index, self._data) if not _is_na(item)]
        if not filtered:
            return Series([], name=self.name)
        new_index, new_data = zip(*filtered)
        return Series(list(new_data), index=list(new_index), name=self.name)

    def apply(self, func: Callable[[Any], Any]) -> "Series":
        return Series([func(item) for item in self._data], index=self.index, name=self.name)

    def astype(self, target: Any) -> "Series":
        if target in (float, "float", "float64"):
            converted = []
            for item in self._data:
                if _is_na(item):
                    converted.append(float("nan"))
                else:
                    converted.append(float(item))
            return Series(converted, index=self.index, name=self.name, dtype=float)
        if target in (str, "str", "string", "object"):
            converted = ["" if _is_na(item) else str(item) for item in self._data]
            return Series(converted, index=self.index, name=self.name, dtype=str)
        return Series([target(item) for item in self._data], index=self.index, name=self.name)

    def value_counts(self, dropna: bool = True) -> "Series":
        counts: Dict[Any, int] = {}
        order: List[Any] = []
        for item in self._data:
            if _is_na(item) and dropna:
                continue
            key = item
            if key not in counts:
                counts[key] = 0
                order.append(key)
            counts[key] += 1
        data = [counts[key] for key in order]
        return Series(data, index=order, name=self.name)

    def unique(self) -> List[Any]:
        seen: List[Any] = []
        for item in self._data:
            if item not in seen:
                seen.append(item)
        return seen

    def reindex(self, new_index: Sequence[Any], fill_value: Any = None) -> "Series":
        mapping = {idx: value for idx, value in zip(self.index, self._data)}
        data = [mapping.get(idx, fill_value) for idx in new_index]
        return Series(data, index=list(new_index), name=self.name)

    def rename_axis(self, axis_name: str) -> "Series":
        new_series = self.copy()
        new_series._axis_name = axis_name
        return new_series

    def reset_index(self, name: str) -> "DataFrame":
        axis_name = self._axis_name or "index"
        return DataFrame({axis_name: self.index, name: self._data})

    def isin(self, values: Iterable[Any]) -> "Series":
        lookup = set(values)
        return Series([item in lookup for item in self._data], index=self.index)

    def sum(self) -> Any:
        total = 0
        for item in self._data:
            if not _is_na(item):
                total += item
        return total

    @property
    def str(self) -> "_StringAccessor":
        return _StringAccessor(self)


class _StringAccessor:
    def __init__(self, series: Series) -> None:
        self._series = series

    def upper(self) -> Series:
        return Series([str(item).upper() if not _is_na(item) else item for item in self._series._data], index=self._series.index, name=self._series.name)

    def strip(self) -> Series:
        return Series([str(item).strip() if not _is_na(item) else item for item in self._series._data], index=self._series.index, name=self._series.name)


class DataFrame:
    def __init__(self, data: Optional[Any] = None) -> None:
        data = data or {}
        self._data: Dict[str, List[Any]] = {}
        self._columns: List[str] = []
        self._rows = 0

        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                column_order: List[str] = []
                for row in data:
                    for key in row.keys():
                        if key not in column_order:
                            column_order.append(key)
                self._columns = column_order
                self._rows = len(data)
                for column in column_order:
                    self._data[column] = [row.get(column) for row in data]
                return
            raise TypeError("Unsupported data structure for DataFrame")

        if isinstance(data, dict):
            self._columns = list(data.keys())
            lengths = {len(list(values)) for values in data.values()} if data else {0}
            if len(lengths) > 1:
                raise ValueError("Columns must all be same length")
            self._rows = next(iter(lengths)) if lengths else 0
            for column, values in data.items():
                self._data[column] = list(values)
            if not data:
                self._rows = 0
            return

        raise TypeError("Unsupported data structure for DataFrame")

    def __len__(self) -> int:
        return self._rows

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"DataFrame(columns={self._columns}, rows={self._rows})"

    @property
    def columns(self) -> List[str]:
        return self._columns.copy()

    @property
    def shape(self) -> tuple[int, int]:
        return (self._rows, len(self._columns))

    def copy(self) -> "DataFrame":
        return DataFrame({col: self._data[col].copy() for col in self._columns})

    def _ensure_length(self, length: int) -> None:
        if self._rows == 0:
            self._rows = length
            return
        if length != self._rows:
            raise ValueError("Length of values does not match DataFrame length")

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            if key not in self._data:
                raise KeyError(key)
            return Series(self._data[key], name=key)
        if isinstance(key, _SeriesClass):
            mask = [bool(item) for item in key]
            return self._filter(mask)
        if isinstance(key, list):
            if key and isinstance(key[0], bool):
                return self._filter([bool(item) for item in key])
            columns = {col: self._data[col] for col in key if col in self._data}
            return DataFrame(columns)
        raise TypeError("Unsupported key type for DataFrame")

    def __setitem__(self, key: str, value: Any) -> None:
        if isinstance(value, _SeriesClass):
            self._ensure_length(len(value))
            self._data[key] = value.tolist()
        elif isinstance(value, list):
            self._ensure_length(len(value))
            self._data[key] = list(value)
        else:
            if self._rows == 0:
                raise ValueError("Cannot broadcast scalar to empty DataFrame")
            self._data[key] = [value for _ in range(self._rows)]
        if key not in self._columns:
            self._columns.append(key)

    def _filter(self, mask: Sequence[bool]) -> "DataFrame":
        if len(mask) != self._rows:
            raise ValueError("Boolean mask must match number of rows")
        filtered = {column: [value for value, keep in zip(values, mask) if keep] for column, values in self._data.items()}
        return DataFrame(filtered)

    def drop(self, *, columns: Sequence[str], inplace: bool = False) -> Optional["DataFrame"]:
        remaining = {col: values for col, values in self._data.items() if col not in columns}
        if inplace:
            self._data = remaining
            self._columns = [col for col in self._columns if col in remaining]
            return None
        return DataFrame(remaining)

    def apply(self, func: Callable[[Dict[str, Any]], Any], axis: int = 0) -> Series:
        if axis != 1:
            raise NotImplementedError("Only axis=1 supported in this simplified implementation")
        results = []
        for row_idx in range(self._rows):
            row = {col: self._data[col][row_idx] for col in self._columns}
            results.append(func(row))
        return Series(results, index=list(range(self._rows)))

    def get(self, column: str, default: Any = None) -> Optional[Series]:
        if column not in self._data:
            return default
        return Series(self._data[column], name=column)

    def memory_usage(self, deep: bool = False) -> Series:
        usage = {col: len(values) * 8 for col, values in self._data.items()}
        return Series(list(usage.values()), index=list(usage.keys()), name="memory")

    def to_csv(self, path: str, index: bool = False) -> None:
        with open(path, "w", newline="") as handle:
            writer = csv.writer(handle)
            if index:
                writer.writerow(["index", *self._columns])
                for idx in range(self._rows):
                    row = [idx] + [self._data[col][idx] for col in self._columns]
                    writer.writerow(row)
            else:
                writer.writerow(self._columns)
                for idx in range(self._rows):
                    writer.writerow([self._data[col][idx] for col in self._columns])

    def to_string(self, index: bool = True) -> str:
        lines = []
        header = ("index\t" if index else "") + "\t".join(self._columns)
        lines.append(header)
        for idx in range(self._rows):
            prefix = f"{idx}\t" if index else ""
            values = "\t".join(str(self._data[col][idx]) for col in self._columns)
            lines.append(prefix + values)
        return "\n".join(lines)

    def to_dicts(self) -> List[Dict[str, Any]]:
        return [
            {col: self._data[col][row] for col in self._columns}
            for row in range(self._rows)
        ]

    def __iter__(self) -> Iterator[Dict[str, Any]]:  # pragma: no cover - convenience
        return iter(self.to_dicts())


_SeriesClass = Series
_DataFrameClass = DataFrame


def Series_constructor(data: Optional[Iterable[Any]] = None, index: Optional[Sequence[Any]] = None, dtype: Any = None, name: Optional[str] = None) -> Series:
    return _SeriesClass(data, index=index, dtype=dtype, name=name)


def DataFrame_constructor(data: Optional[Dict[str, Iterable[Any]]] = None) -> DataFrame:
    return _DataFrameClass(data)


def to_datetime(values: Iterable[Any], errors: str = "raise") -> Series:
    if isinstance(values, _SeriesClass):
        raw = values.tolist()
        index = values.index
    else:
        raw = list(values)
        index = None
    result: List[Optional[Timestamp]] = []
    for item in raw:
        parsed = _coerce_timestamp(item, errors=errors)
        result.append(parsed)
    return Series(result, index=index)


def cut(series: Series, bins: Sequence[float], labels: Sequence[str], right: bool = True) -> Series:
    data = []
    for value in series:
        if _is_na(value):
            data.append(None)
            continue
        placed = False
        for idx in range(len(bins) - 1):
            left = bins[idx]
            right_edge = bins[idx + 1]
            left_ok = value >= left if idx == 0 else value > left
            right_ok = value <= right_edge if right else value < right_edge or idx == len(bins) - 2
            if left_ok and right_ok:
                data.append(labels[idx])
                placed = True
                break
        if not placed:
            data.append(None)
    return Series(data, index=series.index)


def read_csv(path: str, **_: Any) -> DataFrame:
    with open(path, "r", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:  # pragma: no cover - defensive
            raise EmptyDataError("No data") from exc
        columns = {name: [] for name in header}
        row_count = 0
        for row in reader:
            if len(row) != len(header):
                raise ValueError("Row length does not match header")
            for name, value in zip(header, row):
                columns[name].append(value)
            row_count += 1
        if row_count == 0:
            raise EmptyDataError("No data")
        return DataFrame(columns)


def read_excel(path: str, **_: Any) -> DataFrame:  # pragma: no cover - optional functionality
    raise NotImplementedError("Excel support is not available in the simplified pandas implementation")


# Public constructors mimic pandas namespace
DataFrame = DataFrame_constructor
Series = Series_constructor
