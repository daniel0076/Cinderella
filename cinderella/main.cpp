#include "beancount/ccore/data.pb.h"
#include "beancount/cparser/ledger.h"

int main() {
    beancount::Ledger ledger;
    const auto output = std::string{"/tmp/gg"};
    beancount::WriteToText(ledger, output);
    return 0;
}
