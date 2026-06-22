import pandas as pd

from etl_restaurant_times_lookup import (
    get_days_open_list_from_raw_day_string,
    get_open_close_times_from_range,
    restaurant_lookup_etl,
)


def test_get_days_open_list_from_raw_day_range():
    days = get_days_open_list_from_raw_day_string("Mon-Fri")

    assert days == {"m", "tu", "w", "th", "f"}


def test_get_days_open_list_from_raw_standalone_days():
    days = get_days_open_list_from_raw_day_string("Sat, Sun")

    assert days == {"sa", "su"}


def test_get_open_close_times_from_range_normalizes_am_pm():
    hours = get_open_close_times_from_range("11 am - 10:30 pm")

    assert hours == {"open": "11:00", "close": "22:30"}


def test_get_open_close_times_from_range_handles_midnight():
    hours = get_open_close_times_from_range("12 am - 1 am")

    assert hours == {"open": "00:00", "close": "01:00"}


def test_restaurant_lookup_etl_splits_overnight_hours(monkeypatch):
    restaurants = pd.DataFrame(
        [
            {
                "Restaurant Name": "Brady's odd-hour eatery",
                "Hours": "Mon 10 pm - 2 am",
            }
        ]
    )
    monkeypatch.setattr(pd, "read_csv", lambda _: restaurants)

    lookup = restaurant_lookup_etl()

    assert lookup["Late Night Pizza"]["m"] == [{"open": "22:00", "close": "24:00"}]
    assert lookup["Late Night Pizza"]["tu"] == [{"open": "00:00", "close": "02:00"}]
