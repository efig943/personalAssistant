import dateparser
import datetime
import pytz

tz = pytz.timezone('America/Los_Angeles')
now_local = datetime.datetime.now(tz)
print("now_local:", now_local)
dt_obj = dateparser.parse("Thursday 8 pm", settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': now_local, 'TIMEZONE': 'America/Los_Angeles'})
print("dt_obj:", dt_obj)
