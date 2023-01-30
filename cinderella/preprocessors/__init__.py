from .einvoice import Einvoice
from .richart import Richart
from .esun import ESun


def get_preprocessor_classes():
    preprocessors = {
        Einvoice.source_name: Einvoice,
        Richart.source_name: Richart,
        ESun.source_name: ESun,
    }

    return preprocessors
