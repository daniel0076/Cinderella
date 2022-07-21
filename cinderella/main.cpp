#include "beancount/ccore/data.pb.h"
#include "beancount/cparser/ledger.h"
#include <memory>

int main() {
    auto ledger = std::make_unique<beancount::Ledger>();
    auto dir = std::make_unique<beancount::Directive>();
    dir->mutable_date()->set_day(1);
    dir->mutable_date()->set_month(12);
    dir->mutable_date()->set_year(2022);
    dir->mutable_tags();
    dir->mutable_links();
    ledger->directives.emplace_back(dir.get());
    // ledger takes the ownership
    dir.release();
    ledger->options = std::make_shared<beancount::options::Options>();
    ledger->info = std::make_shared<beancount::options::ProcessingInfo>();
    const auto output = std::string{"/tmp/gg"};
    beancount::WriteToText(*ledger, output);
    return 0;
}
