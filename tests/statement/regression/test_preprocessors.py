import filecmp
import pytest
from pathlib import Path
from cinderella.statement.parsers.base import StatementParser
from cinderella.statement.parsers.richart import Richart
from cinderella.statement.parsers.esun import ESun
from cinderella.statement.parsers.einvoice import Einvoice
from cinderella.statement.datatypes import AfterPreprocessAction
from cinderella.ledger.datatypes import StatementType
from cinderella.settings import StatementSettings, PreprocessSettings


@pytest.fixture
def get_statement_path():
    def file_path(source_name: str, statement_type: str, filename: str):
        return Path(__file__).parent / "data" / source_name / statement_type / filename

    return file_path


@pytest.fixture
def gen_settings(tmp_path):
    def gen_settings_impl(
        source_name: str, password: str, statement_type: StatementType
    ):
        proprocessed_statements_dir = tmp_path / "preprocessed_statements"
        settings = StatementSettings(
            "",
            proprocessed_statements_dir.as_posix(),
            "",
            {
                source_name: {
                    statement_type: PreprocessSettings(
                        statement_type, password, AfterPreprocessAction.keep
                    )
                }
            },
        )
        return settings

    return gen_settings_impl


class TestPreProcess:
    @pytest.mark.parametrize(
        "statement_type, target_cls, test_file, password, result_file, expected_file",
        [
            (
                StatementType.receipt,
                Einvoice,
                "test_receipt.csv",
                "",
                "202210.csv",
                "receipt_expected.csv",
            ),
            (
                StatementType.checking,
                ESun,
                "test_checking.html",
                "",
                "202210.csv",
                "bank_expected.csv",
            ),
            (
                StatementType.checking,
                Richart,
                "test_bank_creditcard.zip",
                "password",
                "202210.csv",
                "bank_expected.csv",
            ),
        ],
        ids=["einvoice-receipt", "esun-bank", "richart-bank"],
    )
    def test_preprocess_by_statement_type(
        self,
        get_statement_path,
        gen_settings,
        statement_type,
        target_cls,
        test_file,
        password,
        result_file,
        expected_file,
    ):
        source_name = target_cls.source_name
        parser: StatementParser = target_cls()
        settings: StatementSettings = gen_settings(
            source_name, password, statement_type
        )
        output_dir = Path(
            settings.preprocessed_statement_folder, source_name, statement_type.value
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        if statement_type == StatementType.creditcard:
            func = parser.preprocess_creditcard_statement
        elif statement_type == StatementType.checking:
            func = parser.preprocess_checking_statement
        elif statement_type == StatementType.receipt:
            func = parser.preprocess_receipt_statement
        else:
            assert False, "Unsupported statement type"

        result = func(
            get_statement_path(source_name, statement_type.value, test_file),
            output_dir,
            settings.preprocess_settings[source_name][statement_type],
        )

        result_path = Path(
            settings.preprocessed_statement_folder,
            source_name,
            statement_type.value,
            result_file,
        )
        expected_path = get_statement_path(source_name, "expected", expected_file)

        assert result.success
        assert result_path.exists()
        assert filecmp.cmp(result_path, expected_path, shallow=False)
