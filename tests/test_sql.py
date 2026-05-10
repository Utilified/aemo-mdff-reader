"""Tests for the optional :mod:`nem12_reader.sql` package.

These checks run without ``pymysql`` installed. They confirm:

1. Importing ``nem12_reader.sql`` does not pull in ``pymysql`` eagerly.
2. ``QueryBuilder`` and ``COLUMNS`` are usable from the package.
3. Touching ``Storer`` / ``DBCredentials`` raises a clear error when
   ``pymysql`` is not available, rather than crashing at import time.
"""

from __future__ import annotations

import importlib
import sys

import pytest


def test_sql_import_does_not_load_pymysql():
    # Drop any prior cached module to force a clean import.
    for name in list(sys.modules):
        if name.startswith("nem12_reader.sql") or name == "pymysql":
            sys.modules.pop(name, None)
    mod = importlib.import_module("nem12_reader.sql")
    assert "pymysql" not in sys.modules, (
        "Importing nem12_reader.sql must not eagerly import pymysql"
    )
    # Public symbols defined in the lazy __init__ should be visible.
    assert hasattr(mod, "QueryBuilder")
    assert hasattr(mod, "COLUMNS")


def test_query_builder_inserts():
    from nem12_reader.sql import QueryBuilder

    rows = [["test.csv", "NEM12", '"date"', "X", "Y"]]
    sql = QueryBuilder.insert_query("imports", rows)
    assert "INSERT IGNORE INTO `imports`" in sql
    assert "filename" in sql


def test_storer_attribute_lazy_loads():
    # If pymysql is not installed, accessing Storer should raise ImportError
    # only at access time, not at module import time.
    pytest.importorskip("nem12_reader.sql")
    import nem12_reader.sql as sql_mod

    if "pymysql" in sys.modules:
        # If pymysql is available in the test env, we can at least confirm
        # the symbol resolves to something callable.
        cls = sql_mod.Storer
        assert callable(cls)
        return
    with pytest.raises((ImportError, ModuleNotFoundError)):
        _ = sql_mod.Storer
