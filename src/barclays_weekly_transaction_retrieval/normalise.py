from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .models import TransactionRow


def map_transaction(run_id: str, account_id: str, raw: dict[str, Any]) -> TransactionRow:
    amount_obj = _dict(raw.get("Amount"))
    amount = str(amount_obj.get("Amount", "0"))
    currency = str(amount_obj.get("Currency", ""))

    indicator = str(raw.get("CreditDebitIndicator", ""))
    signed_amount = _signed_amount(amount, indicator)

    bank_code_obj = _dict(raw.get("BankTransactionCode"))
    bank_code = _join_code_parts(bank_code_obj.get("Code"), bank_code_obj.get("SubCode"))
    proprietary_code = str(_dict(raw.get("ProprietaryBankTransactionCode")).get("Code", "") or "")

    transaction_id = str(raw.get("TransactionId") or raw.get("EntryReference") or "")
    remittance_reference = _remittance_reference(raw)

    return TransactionRow(
        run_id=run_id,
        account_id=str(raw.get("AccountId") or account_id),
        transaction_id=transaction_id,
        booking_date_time=str(raw.get("BookingDateTime", "")),
        value_date_time=str(raw.get("ValueDateTime", "")),
        credit_debit_indicator=indicator,
        amount=amount,
        signed_amount=signed_amount,
        currency=currency,
        status=str(raw.get("Status", "")),
        description=str(raw.get("TransactionInformation", "")),
        bank_transaction_code=bank_code,
        proprietary_bank_transaction_code=proprietary_code,
        remittance_reference=remittance_reference,
    )


def _signed_amount(amount: str, indicator: str) -> str:
    try:
        value = Decimal(amount)
    except InvalidOperation:
        return amount

    if indicator.lower() == "debit":
        value = -abs(value)
    elif indicator.lower() == "credit":
        value = abs(value)

    return format(value, "f")


def _join_code_parts(*parts: object) -> str:
    return ".".join(str(part) for part in parts if part)


def _remittance_reference(raw: dict[str, Any]) -> str:
    remittance = _dict(raw.get("RemittanceInformation"))
    unstructured = remittance.get("Unstructured", [])
    if isinstance(unstructured, list) and unstructured:
        return " | ".join(str(value) for value in unstructured)
    if isinstance(unstructured, str):
        return unstructured
    return ""


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
