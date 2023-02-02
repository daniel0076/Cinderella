from collections import namedtuple
from pathlib import Path
import pytest
import os
from unittest.mock import patch, MagicMock

from cinderella.preprocessor import StatementPreprocessor
from cinderella.preprocessors.base import ProcessorBase, ProcessedResult
from cinderella.settings import StatementSettings, RawStatementProcessSettings
from cinderella.datatypes import AfterProcessedAction, StatementType


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
    raw_statement_dir = tmp_path / "raw" / "bank" / source_name
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
            source_name: [
                RawStatementProcessSettings(
                    StatementType.bank, "", AfterProcessedAction.move
                )
            ]
        },
    )

    return settings


class TestStatementProcessor:
    @patch("cinderella.preprocessor.get_preprocessor_classes")
    def test_statement_processor(
        self, mock_method, source_name, statement_dir, settings
    ):
        # prepare
        mock_method.return_value = {source_name: MagicMock()}

        # test
        statement_processor = StatementPreprocessor(settings)
        statement_processor.process()

        # assert
        mock_preprocessor = statement_processor.preprocessors[source_name]
        mock_preprocessor.process.assert_called_once_with(statement_dir.mock_statement)


class TestProcessorBase:
    # if __abstractmethod__ is non-empty, the class is considered abstract
    @patch.multiple(ProcessorBase, __abstractmethods__=set(), source_name="mock_source")
    @patch.object(ProcessorBase, "post_process")
    @patch.object(ProcessorBase, "process_bank")
    def test_process_success(self, process_bank, post_process, statement_dir, settings):
        # prepare
        process_bank.return_value = ProcessedResult(True, "success")

        # test
        mock_preprocessor = ProcessorBase(settings)
        result = mock_preprocessor.process(statement_dir.mock_statement)

        # assert
        assert result == process_bank.return_value
        process_bank.assert_called_once_with(
            statement_dir.mock_statement,
            mock_preprocessor.settings_by_type[StatementType.bank],
        )
        post_process.assert_called_once_with(
            statement_dir.mock_statement,
            mock_preprocessor.settings_by_type[StatementType.bank],
        )

    @patch.multiple(ProcessorBase, __abstractmethods__=set(), source_name="mock_source")
    @patch.object(ProcessorBase, "post_process")
    @patch.object(ProcessorBase, "process_bank")
    def test_process_failed(self, process_bank, post_process, statement_dir, settings):
        # prepare
        process_bank.return_value = ProcessedResult(False, "failed")

        # test
        mock_preprocessor = ProcessorBase(settings)
        result = mock_preprocessor.process(statement_dir.mock_statement)

        # assert
        assert result == process_bank.return_value
        process_bank.assert_called_once_with(
            statement_dir.mock_statement,
            mock_preprocessor.settings_by_type[StatementType.bank],
        )
        post_process.assert_not_called()

    @pytest.mark.parametrize(
        "operation",
        [
            AfterProcessedAction.keep,
            AfterProcessedAction.delete,
            AfterProcessedAction.move,
        ],
    )
    @patch.multiple(ProcessorBase, __abstractmethods__=set(), source_name="mock_source")
    def test_post_process(self, statement_dir, settings, source_name, operation):
        # test
        mock_preprocessor = ProcessorBase(settings)
        statement_settings = mock_preprocessor.settings_by_type[StatementType.bank]
        statement_settings.after_processed = operation
        mock_preprocessor.post_process(statement_dir.mock_statement, statement_settings)

        # assert
        if operation == AfterProcessedAction.keep:
            assert statement_dir.mock_statement.exists()
        elif operation == AfterProcessedAction.delete:
            assert not statement_dir.mock_statement.exists()
        elif operation == AfterProcessedAction.move:
            assert not statement_dir.mock_statement.exists()
            # should be moved
            assert Path(
                statement_dir.backup_statement_dir
                / StatementType.bank.value
                / source_name
                / statement_dir.mock_statement.name
            ).exists()
