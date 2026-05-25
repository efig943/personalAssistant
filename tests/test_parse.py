import datetime
import pytz
import dateparser
import sys
tz_name = "America/Los_Angeles"
tz = pytz.timezone(tz_name)
now_local = datetime.datetime.now(tz)
dt_obj = dateparser.parse(
    "Tuesday 4pm",
    settings={
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": now_local,
        "TIMEZONE": tz_name,
    },
)
if dt_obj:
    if not dt_obj.tzinfo:
        dt_obj = tz.localize(dt_obj)
    print(dt_obj.astimezone(datetime.timezone.utc).isoformat())
else:
    print("None")
