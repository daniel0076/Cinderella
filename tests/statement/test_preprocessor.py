from collections import namedtuple
from pathlib import Path
import pytest
from unittest.mock import patch

from cinderella.statement.datatypes import AfterPreprocessAction
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
                StatementType.checking: PreprocessSettings(
                    StatementType.checking, "", AfterPreprocessAction.move
                )
            }
        },
    )

    return settings


# TODO: fix tests
# class TestProcessorBase:
#    # if __abstractmethod__ is non-empty, the class is considered abstract
#    @patch.multiple(
#        PreprocessorBase, __abstractmethods__=set(), source_name="mock_source"
#    )
#    @patch.object(PreprocessorBase, "post_process")
#    @patch.object(PreprocessorBase, "process_checking")
#    def test_process_success(
#        self, process_checking, post_process, statement_dir, settings
#    ):
#        # prepare
#        process_checking.return_value = ProcessResult(True, "success")
#
#        # test
#        mock_preprocessor = PreprocessorBase(settings)
#        result = mock_preprocessor.process(statement_dir.mock_statement)
#        print(result)
#
#        # assert
#        assert result == process_checking.return_value
#        process_checking.assert_called_once_with(
#            statement_dir.mock_statement,
#            mock_preprocessor.settings_by_type[StatementType.checking],
#        )
#        post_process.assert_called_once_with(
#            statement_dir.mock_statement,
#            mock_preprocessor.settings_by_type[StatementType.checking],
#        )
#
#    @patch.multiple(
#        PreprocessorBase, __abstractmethods__=set(), source_name="mock_source"
#    )
#    @patch.object(PreprocessorBase, "post_process")
#    @patch.object(PreprocessorBase, "process_checking")
#    def test_process_failed(
#        self, process_checking, post_process, statement_dir, settings
#    ):
#        # prepare
#        process_checking.return_value = ProcessResult(False, "failed")
#
#        # test
#        mock_preprocessor = PreprocessorBase(settings)
#        result = mock_preprocessor.process(statement_dir.mock_statement)
#
#        # assert
#        assert result == process_checking.return_value
#        process_checking.assert_called_once_with(
#            statement_dir.mock_statement,
#            mock_preprocessor.settings_by_type[StatementType.checking],
#        )
#        post_process.assert_not_called()
#
#    @pytest.mark.parametrize(
#        "operation",
#        [
#            AfterPreprocessAction.keep,
#            AfterPreprocessAction.delete,
#            AfterPreprocessAction.move,
#        ],
#    )
#    @patch.multiple(
#        PreprocessorBase, __abstractmethods__=set(), source_name="mock_source"
#    )
