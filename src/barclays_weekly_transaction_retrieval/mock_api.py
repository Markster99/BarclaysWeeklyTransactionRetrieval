from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .dates import DateWindow


@dataclass
class MockBarclaysApiClient:
    """Small in-memory client used for tests and public portfolio demos."""

    def list_accounts(self) -> list[dict[str, Any]]:
        return [
            {
                "AccountId": "mock-operating-001",
                "Currency": "GBP",
                "Nickname": "Operating Account",
                "AccountTypeCode": "Business",
            },
            {
                "AccountId": "mock-rent-002",
                "Currency": "GBP",
                "Nickname": "Collections Account",
                "AccountTypeCode": "Business",
            },
        ]

    def get_balances(self, account_id: str) -> list[dict[str, Any]]:
        return [
            {
                "AccountId": account_id,
                "CreditDebitIndicator": "Credit",
                "Type": "CLBD",
                "Amount": {"Amount": "12500.00", "Currency": "GBP"},
            }
        ]

    def get_transactions(self, account_id: str, window: DateWindow) -> list[dict[str, Any]]:
        first = window.start + timedelta(days=1, hours=10)
        second = window.start + timedelta(days=3, hours=15, minutes=30)

        return [
            {
                "AccountId": account_id,
                "TransactionId": f"{account_id}-txn-001",
                "CreditDebitIndicator": "Credit",
                "Status": "Booked",
                "BookingDateTime": first.isoformat(),
                "ValueDateTime": first.isoformat(),
                "Amount": {"Amount": "2420.00", "Currency": "GBP"},
                "TransactionInformation": "Sample receipt",
                "BankTransactionCode": {"Code": "PMNT", "SubCode": "RCDT"},
                "ProprietaryBankTransactionCode": {"Code": "BGC", "Issuer": "Barclays"},
                "RemittanceInformation": {"Unstructured": ["INV-10001"]},
            },
            {
                "AccountId": account_id,
                "TransactionId": f"{account_id}-txn-002",
                "CreditDebitIndicator": "Debit",
                "Status": "Booked",
                "BookingDateTime": second.isoformat(),
                "ValueDateTime": second.isoformat(),
                "Amount": {"Amount": "118.42", "Currency": "GBP"},
                "TransactionInformation": "Sample supplier payment",
                "BankTransactionCode": {"Code": "PMNT", "SubCode": "ICDT"},
                "ProprietaryBankTransactionCode": {"Code": "FPS", "Issuer": "Barclays"},
                "RemittanceInformation": {"Unstructured": ["SUPPLIER-REF-42"]},
            },
        ]
