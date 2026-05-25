import datetime
import pytz
import dateparser
import sys
tz_name = "America/Los_Angeles"
tz = pytz.timezone(tz_name)
now_local = datetime.datetime.now(tz)
dt_obj = dateparser.parse(
    "That works",
    settings={
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": now_local,
        "TIMEZONE": tz_name,
    },
)
print("Parsed:", dt_obj)
