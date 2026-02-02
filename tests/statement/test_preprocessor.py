from collections import namedtuple
from pathlib import Path
import pytest
from unittest.mock import patch

from cinderella.ledger.datatypes import StatementType
from cinderella.settings import StatementSettings, PreprocessSettings


@pytest.fixture
def source_name():
    return "mock_source"


@pytest.fixture(scope="function")
def statement_dir(tmp_path, source_name):
    result = namedtuple(
        "StatementDir",
        [
            "raw_statement_dir",
            "backup_statement_dir",
            "mock_statement",
            "hidden_statement",
        ],
    )
    # prepare
    raw_statement_dir = tmp_path / "raw" / source_name / "checking"
    raw_statement_dir.mkdir(parents=True)
    backup_statement_dir = tmp_path / "backup"
    backup_statement_dir.mkdir(parents=True)
    mock_statement = raw_statement_dir / "202301.csv"
    mock_statement.touch()
    hidden_statement = raw_statement_dir / ".hidden.csv"
    hidden_statement.touch()

    return result(
        raw_statement_dir, backup_statement_dir, mock_statement, hidden_statement
    )


@pytest.fixture()
def settings(statement_dir, source_name) -> StatementSettings:
    settings = StatementSettings(
        statement_dir.raw_statement_dir.as_posix(),
        "",
        statement_dir.backup_statement_dir.as_posix(),
        {
            source_name: {
                StatementType.checking: PreprocessSettings(StatementType.checking, "")
            }
        },
    )

    return settings
