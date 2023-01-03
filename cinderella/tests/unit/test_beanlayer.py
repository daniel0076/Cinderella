from decimal import Decimal
from datetime import datetime
from copy import deepcopy

from beancount.core.amount import Amount, sub
from beancount.core.data import Transaction, Posting


class TestBeanLayer:
    def test_make_amount(self, beancount_api):
        number = Decimal(100)
        amount = beancount_api.make_amount(number, "TWD")
        assert amount == Amount(number, "TWD")

    def test_make_posting(self, beancount_api, sample_account, sample_amount):
        account = sample_account
        posting = beancount_api.make_posting(account, sample_amount)
        assert posting == Posting(account, sample_amount, None, None, None, {})

    def test_make_transaction(
        self, beancount_api, sample_posting, sample_transaction_narration
    ):
        title = sample_transaction_narration
        meta = {}
        date = datetime.now().date()
        trans = beancount_api.make_transaction(date, title, [sample_posting])
        assert trans == Transaction(
            meta, date, "*", None, title, set(), set(), [sample_posting]
        )

    def test_add_transaction_comment(self, beancount_api, sample_transaction):
        beancount_api.add_transaction_comment(sample_transaction, "test")
        assert sample_transaction.meta == {";1": "test"}

        beancount_api.add_transaction_comment(sample_transaction, "test")
        assert sample_transaction.meta == {";1": "test", ";2": "test"}

    def test_add_posting_comment(self, beancount_api, sample_transaction):
        beancount_api.add_posting_comment(sample_transaction, "test")
        assert sample_transaction.postings[0].meta == {";1": "test"}

        beancount_api.add_posting_comment(sample_transaction, "test")
        assert sample_transaction.postings[0].meta == {";1": "test", ";2": "test"}

    def test_add_posting_comment_different_transactions(
        self, beancount_api, sample_transaction, another_transaction
    ):
        beancount_api.add_posting_comment(sample_transaction, "sample")
        beancount_api.add_posting_comment(another_transaction, "another")
        assert sample_transaction.postings[0].meta == {";1": "sample"}
        assert another_transaction.postings[0].meta == {";1": "another"}

    def test_add_posting_amount(self, beancount_api, sample_transaction):
        origin_amount = sample_transaction.postings[0].units
        beancount_api.add_posting_amount(sample_transaction, Decimal(1.0))
        result = Amount(Decimal(1), "TWD")
        assert sub(sample_transaction.postings[0].units, origin_amount) == result

    def test_add_transaction_posting_with_posting(
        self, beancount_api, sample_transaction, another_posting
    ):
        index = beancount_api.add_transaction_posting(
            sample_transaction, posting=another_posting
        )
        assert index == 1
        assert sample_transaction.postings[index] == another_posting

    def test_create_and_add_transaction_posting(
        self,
        beancount_api,
        sample_transaction,
        another_account,
        another_amount,
        another_posting,
    ):
        index = beancount_api.create_and_add_transaction_posting(
            sample_transaction,
            another_account,
            another_amount.number,
            another_amount.currency,
        )
        assert index == 1
        assert sample_transaction.postings[index] == another_posting

    def test_merge_duplicated_transactions(
        self, beancount_api, sample_transaction, sample_account
    ):
        removed_trans = deepcopy(sample_transaction)
        appended_trans = deepcopy(sample_transaction)
        beancount_api.add_transaction_comment(removed_trans, "removed")
        beancount_api.add_transaction_comment(appended_trans, "appended")
        beancount_api.add_posting_comment(removed_trans, "removed")
        beancount_api.add_posting_comment(appended_trans, "appended")

        beancount_api.merge_transactions(
            appended_trans, removed_trans, keep_dest_accounts=False
        )
        assert appended_trans.meta == {";1": "appended", ";2": "removed"}
        assert appended_trans.postings[0].account == sample_account
        assert appended_trans.postings[0].meta == {";1": "appended", ";2": "removed"}

    def test_merge_duplicated_transactions_different_round(
        self, beancount_api, sample_transaction, sample_account
    ):
        amount1 = beancount_api.make_amount(Decimal("100.0"), "TWD")
        removed_trans = deepcopy(sample_transaction)
        appended_trans = deepcopy(sample_transaction)

        removed_trans.postings[0] = removed_trans.postings[0]._replace(units=amount1)

        beancount_api.merge_transactions(
            appended_trans, removed_trans, keep_dest_accounts=False
        )
        assert appended_trans.postings[0].account == sample_account

    def test_find_keyword(
        self, beancount_api, sample_transaction, sample_transaction_narration
    ):
        assert beancount_api.find_keyword(
            sample_transaction, sample_transaction_narration
        )
        assert beancount_api.find_keyword(
            sample_transaction, sample_transaction_narration[1:3]
        )
        # test regex support
        assert beancount_api.find_keyword(sample_transaction, ".*")
        assert not beancount_api.find_keyword(
            sample_transaction, f"[^{sample_transaction_narration}]"
        )
