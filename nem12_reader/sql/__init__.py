"""Optional SQL persistence layer.

Importing this subpackage does NOT eagerly import :mod:`pymysql`.
The dependency is only required when you actually instantiate
:class:`Storer`. Install with ``pip install nem12-reader[mysql]``.
"""

from __future__ import annotations

from .query import COLUMNS, QueryBuilder

__all__ = ["COLUMNS", "QueryBuilder", "Storer", "DBCredentials"]


def __getattr__(name):
    # Lazy import so that ``import nem12_reader.sql`` does not require pymysql
    # to be installed unless the caller actually uses the Storer.
    if name in ("Storer", "DBCredentials"):
        from .store import Storer, DBCredentials  # noqa: WPS433
        return {"Storer": Storer, "DBCredentials": DBCredentials}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
