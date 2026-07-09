# Barclays Weekly Transaction Retrieval

Python automation for weekly Barclays API transaction retrieval, producing reconciliation-ready CSV outputs for Finance review.

This project was built around a practical Finance operations problem: recurring bank transaction downloads are slow, repetitive and difficult to evidence consistently. The service calculates a reporting window, retrieves account-level transaction data, normalises the API response and writes controlled output files that can be reviewed before reconciliation.

The current repo is designed to be safe for a public portfolio. It includes a mock client and sample payloads so the workflow can be run without Barclays credentials or real bank data.

## What the project does

- Calculates previous-week and previous-month reporting windows.
- Retrieves account and transaction data from a Barclays-style Account and Transactions API.
- Supports mock, sandbox and live configuration modes.
- Adds financial API request headers such as interaction IDs and auth timestamps.
- Normalises nested transaction JSON into flat Finance-friendly rows.
- Produces CSV and JSONL transaction extracts.
- Writes a manifest for each run, including date window, accounts requested and row counts.
- Keeps a small local state file to reduce duplicate exports.
- Includes tests for date windows, transaction mapping, state handling and mock pipeline output.
- Includes GitHub Actions for CI and an optional scheduled weekly workflow.

## Why this matters

Manual bank statement downloads are workable for a small number of accounts, but they do not scale well. The aim here is to make the extraction step repeatable and auditable while keeping the final review with Finance.

This is intentionally a read-only workflow. It does not post journals, approve payments or update any accounting system.

## Project structure

```text
.
├── .github/workflows/
├── docs/
├── examples/
├── scripts/
├── src/barclays_weekly_transaction_retrieval/
└── tests/
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

barclays-weekly doctor
barclays-weekly window --mode previous-week
barclays-weekly run --mock
```

The mock run writes output to `data/out/` and does not call Barclays.

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

For a mock run, no credentials are needed.

For sandbox/live use, provide credentials through environment variables, a local `.env` file or a CI secret store. Do not commit real credentials.

```bash
BARCLAYS_ENVIRONMENT=sandbox
BARCLAYS_ACCESS_TOKEN=replace-with-token
BARCLAYS_ACCOUNT_IDS=account-001,account-002
BARCLAYS_OUTPUT_DIR=data/out
BARCLAYS_STATE_FILE=data/state/run_state.json
```

## Example commands

Run a weekly mock export:

```bash
barclays-weekly run --mock --window previous-week
```

Run a previous-month export:

```bash
barclays-weekly run --mock --window previous-month
```

Run a specific date range:

```bash
barclays-weekly run --mock --from-date 2026-07-01 --to-date 2026-07-08
```

Run tests:

```bash
pytest
```

Run the local secret check before publishing:

```bash
python scripts/check_no_secrets.py
```

## Public repo safety

This repository should not contain client IDs, client secrets, access tokens, private keys, transport certificates, Barclays dashboard screenshots, real account IDs or real transaction data.

## Disclaimer

This is an independent portfolio project and is not an official Barclays, Legal & General or Open Banking implementation. It is intended to demonstrate a finance automation pattern using public/sandbox-style API workflows and mock data.
