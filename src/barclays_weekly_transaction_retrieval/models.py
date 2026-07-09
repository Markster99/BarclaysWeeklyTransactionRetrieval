from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TransactionRow:
    run_id: str
    account_id: str
    transaction_id: str
    booking_date_time: str
    value_date_time: str
    credit_debit_indicator: str
    amount: str
    signed_amount: str
    currency: str
    status: str
    description: str
    bank_transaction_code: str
    proprietary_bank_transaction_code: str
    remittance_reference: str

    def as_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}

    @property
    def idempotency_key(self) -> str:
        return "|".join(
            [
                self.account_id,
                self.transaction_id,
                self.booking_date_time,
                self.signed_amount,
            ]
        )
