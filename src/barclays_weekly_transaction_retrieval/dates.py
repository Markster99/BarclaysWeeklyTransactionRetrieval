from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone


UTC = timezone.utc


@dataclass(frozen=True)
class DateWindow:
    label: str
    start: datetime
    end: datetime

    def as_query_params(self) -> dict[str, str]:
        return {
            "fromBookingDateTime": self.start.isoformat(),
            "toBookingDateTime": self.end.isoformat(),
        }

    def filename_part(self) -> str:
        return f"{self.label}_{self.start.date()}_to_{self.end.date()}"


def previous_week(as_of: date | None = None) -> DateWindow:
    as_of = as_of or datetime.now(UTC).date()
    current_monday = as_of - timedelta(days=as_of.weekday())
    prior_monday = current_monday - timedelta(days=7)
    return DateWindow(
        label="previous_week",
        start=datetime.combine(prior_monday, time.min, tzinfo=UTC),
        end=datetime.combine(current_monday, time.min, tzinfo=UTC),
    )


def previous_month(as_of: date | None = None) -> DateWindow:
    as_of = as_of or datetime.now(UTC).date()
    first_current_month = as_of.replace(day=1)
    last_previous_month = first_current_month - timedelta(days=1)
    first_previous_month = last_previous_month.replace(day=1)
    return DateWindow(
        label="previous_month",
        start=datetime.combine(first_previous_month, time.min, tzinfo=UTC),
        end=datetime.combine(first_current_month, time.min, tzinfo=UTC),
    )


def custom_window(from_date: date, to_date: date) -> DateWindow:
    if to_date <= from_date:
        raise ValueError("to_date must be after from_date")
    return DateWindow(
        label="custom",
        start=datetime.combine(from_date, time.min, tzinfo=UTC),
        end=datetime.combine(to_date, time.min, tzinfo=UTC),
    )


def resolve_window(mode: str, as_of: date | None = None) -> DateWindow:
    if mode == "previous-week":
        return previous_week(as_of)
    if mode == "previous-month":
        return previous_month(as_of)
    raise ValueError("mode must be previous-week or previous-month")
