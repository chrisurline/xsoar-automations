# intended to be used as a transformer - calculates days until or days since. 

from typing import Dict, Any
import traceback
from datetime import datetime
import dateparser

def main():
    try:
        # retrieve the 'timestamp' argument
        args = demisto.args()
        timestamp_str = args.get('timestamp')
        if not timestamp_str:
            return_error('No timestamp provided. Please provide a valid timestamp.')

        # parse timestamp
        input_time = dateparser.parse(timestamp_str)
        if not input_time:
            return_error('Failed to parse the provided timestamp.')

        # remove timestamp
        if input_time.tzinfo is not None:
            input_time = input_time.replace(tzinfo=None)

        # get current datetime
        now = datetime.now()

        # calculate the difference in days
        delta = input_time - now
        days_difference = delta.days

        # construct the output message
        if days_difference > 0:
            message = f"{days_difference} day(s) until"
        elif days_difference < 0:
            message = f"{abs(days_difference)} day(s) ago"
        else:
            message = "today"

        # return the result
        demisto.results({
            'Type': 4,
            'ContentsFormat': 'text',
            'Contents': message
        })

    except Exception as e:
        return_error(f'Failed to execute the script. Error: {str(e)}')

def return_error(message):
    demisto.error(message)
    demisto.results({
        'Type': 4,
        'ContentsFormat': 'text',
        'Contents': message
    })

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()