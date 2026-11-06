from datetime import date, datetime, timezone


class SystemClock:
    def hoy(self) -> date:
        return datetime.now(timezone.utc).date()

    def ahora(self) -> datetime:
        return datetime.now(timezone.utc)
