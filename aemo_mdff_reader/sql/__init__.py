"""Optional SQL persistence layer.

Importing this subpackage does NOT eagerly import :mod:`pymysql`.
The dependency is only required when you actually instantiate
:class:`Storer`. Install with ``pip install aemo-mdff-reader[mysql]``.
"""

from __future__ import annotations

from .query import COLUMNS, QueryBuilder

__all__ = ["COLUMNS", "DBCredentials", "QueryBuilder", "Storer"]


def __getattr__(name):
    # Lazy import so that ``import aemo_mdff_reader.sql`` does not require pymysql
    # to be installed unless the caller actually uses the Storer.
    if name in ("Storer", "DBCredentials"):
        from .store import DBCredentials, Storer

        return {"Storer": Storer, "DBCredentials": DBCredentials}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
