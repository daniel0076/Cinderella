import filecmp
import pytest
from pathlib import Path
from cinderella.statement.preprocessors.richart import Richart as RichartPreprocessor
from cinderella.statement.preprocessors.esun import ESun as ESunPreprocessor
from cinderella.statement.preprocessors.einvoice import Einvoice as EinvoicePreprocessor
from cinderella.statement.datatypes import AfterProcessedAction
from cinderella.ledger.datatypes import StatementType
from cinderella.settings import StatementSettings, RawStatementProcessSettings


@pytest.fixture
def get_data():
    def file_path(source_name: str, direction: str, filename: str):
        return Path(__file__).parent / "data" / source_name / direction / filename

    return file_path


@pytest.fixture
def gen_settings(tmp_path):
    def gen_settings_impl(
        source_name: str, password: str, statement_type: StatementType
    ):
        ready_dir = tmp_path / "ready"
        settings = StatementSettings(
            "",
            ready_dir.as_posix(),
            "",
            {
                source_name: [
                    RawStatementProcessSettings(
                        statement_type, password, AfterProcessedAction.keep
                    )
                ]
            },
        )
        return settings

    return gen_settings_impl


class TestPreProcessor:
    @pytest.mark.parametrize(
        "source_name, statement_type, target_cls, test_file, password, result_file, expected_file",
        [
            (
                "einvoice",
                StatementType.receipt,
                EinvoicePreprocessor,
                "test_receipt.csv",
                "",
                "202210.csv",
                "receipt_expected.csv",
            ),
            (
                "esun",
                StatementType.bank,
                ESunPreprocessor,
                "test_bank.html",
                "",
                "202210.csv",
                "bank_expected.csv",
            ),
            (
                "richart",
                StatementType.bank,
                RichartPreprocessor,
                "test_bank_creditcard.zip",
                "password",
                "202210.csv",
                "bank_expected.csv",
            ),
            (
                "richart",
                StatementType.creditcard,
                RichartPreprocessor,
                "test_bank_creditcard.zip",
                "password",
                "202210.csv",
                "creditcard_expected.csv",
            ),
        ],
        ids=["einvoice-receipt", "esun-bank", "richart-bank", "richart-creditcard"],
    )
    def test_process(
        self,
        get_data,
        gen_settings,
        source_name,
        statement_type,
        target_cls,
        test_file,
        password,
        result_file,
        expected_file,
    ):
        settings = gen_settings(source_name, password, statement_type)
        preprocessor = target_cls(settings)
        result = preprocessor.process(get_data(source_name, "input", test_file))

        result_path = Path(
            settings.ready_statement_folder,
            statement_type.value,
            source_name,
            result_file,
        )
        expected_path = get_data(source_name, "output", expected_file)

        assert result.success
        assert result_path.exists()
        assert filecmp.cmp(result_path, expected_path, shallow=False)
