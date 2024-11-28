# input a timestamp and get back a string loosely representing how long ago or how far in the future 
# ex. "3 days ago", "19 years ago", "9 days from now"

from typing import Dict, Any
import traceback
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta

def time_diff_desc(timestamp_str):
    try:
        # parse input timestamp_str
        timestamp = parser.parse(timestamp_str)
    except Exception as e:
        return_error(f"Error parsing date: {str(e)}")

    # get current t ime with timezone from input
    if timestamp.tzinfo is None:
        now = datetime.now()
    else:
        now = datetime.now(timestamp.tzinfo)

    # calculate diff
    if now >= timestamp:
        diff = relativedelta(now, timestamp)
        suffix = "ago"
    else:
        diff = relativedelta(timestamp, now)
        suffix = "from now"

    # build output string
    if diff.years > 0:
        unit = "year" if diff.years == 1 else "years"
        return f"{diff.years} {unit} {suffix}"
    elif diff.months > 0:
        unit = "month" if diff.months == 1 else "months"
        return f"{diff.months} {unit} {suffix}"
    elif diff.days > 0:
        unit = "day" if diff.days == 1 else "days"
        return f"{diff.days} {unit} {suffix}"
    elif diff.hours > 0:
        unit = "hour" if diff.hours == 1 else "hours"
        return f"{diff.hours} {unit} {suffix}"
    elif diff.minutes > 0:
        unit = "minute" if diff.minutes == 1 else "minutes"
        return f"{diff.minutes} {unit} {suffix}"
    else:
        return "Just now"

def main():
    try:
        # get timestamp from demisto args
        args = demisto.args()
        timestamp_str = args.get('timestamp')

        if not timestamp_str:
            return_error('No timestamp provided.')

        result = time_diff_desc(timestamp_str)

        demisto.results(result)

    except Exception as e:
        return_error(f'Failed to execute script. Error: {str(e)}')

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
