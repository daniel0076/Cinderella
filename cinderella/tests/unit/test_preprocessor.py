from collections import namedtuple
import pytest
from unittest.mock import patch, MagicMock

from cinderella.preprocessor import StatementPreprocessor
from cinderella.preprocessors.base import ProcessorBase, ProcessedResult
from cinderella.settings import StatementSettings, RawStatementProcessSettings
from cinderella.datatypes import AfterProcessedAction, StatementType


@pytest.fixture(scope="function")
def statement_dir(tmp_path):
    result = namedtuple(
        "StatementDir", ["mock_statement", "mock_statement_dir", "hidden_statement"]
    )
    # prepare
    mock_statement_dir = tmp_path / "bank" / "mock_source"
    mock_statement_dir.mkdir(parents=True)
    mock_statement = mock_statement_dir / "202301.csv"
    mock_statement.touch()
    hidden_statement = mock_statement_dir / ".hidden.csv"
    hidden_statement.touch()

    return result(mock_statement, mock_statement_dir, hidden_statement)


@pytest.fixture()
def settings(statement_dir) -> StatementSettings:
    settings = StatementSettings(
        statement_dir.mock_statement_dir.as_posix(),
        "",
        "",
        {
            "mock_source": [
                RawStatementProcessSettings(
                    StatementType.bank, "", AfterProcessedAction.move
                )
            ]
        },
    )

    return settings


class TestStatementProcessor:
    @patch("cinderella.preprocessor.get_preprocessor_classes")
    def test_statement_processor(self, mock_method, statement_dir, settings):
        # prepare
        mock_method.return_value = {"mock_source": MagicMock()}

        # test
        statement_processor = StatementPreprocessor(settings)
        statement_processor.process()

        # assert
        mock_preprocessor = statement_processor.preprocessors["mock_source"]
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

    @patch.multiple(ProcessorBase, __abstractmethods__=set(), source_name="mock_source")
    def test_post_process(self, statement_dir, settings):
        # test
        mock_preprocessor = ProcessorBase(settings)
        statement_settings = mock_preprocessor.settings_by_type[StatementType.bank]
        mock_preprocessor.post_process(statement_dir.mock_statement, statement_settings)
