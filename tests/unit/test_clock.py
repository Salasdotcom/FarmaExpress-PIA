from datetime import date, datetime

from src.infrastructure.clock import SystemClock


def test_system_clock():
    c = SystemClock()
    assert isinstance(c.hoy(), date) and isinstance(c.ahora(), datetime)
