# intended to be used as a transformer - calculates days until or days since. 

from typing import Dict, Any
import traceback
from datetime import datetime
import dateparser

def main():
    try:
        # Retrieve the 'timestamp' argument
        args = demisto.args()
        timestamp_str = args.get('timestamp')
        if not timestamp_str:
            return_error('No timestamp provided. Please provide a valid timestamp.')

        # Parse the timestamp into a datetime object
        input_time = dateparser.parse(timestamp_str)
        if not input_time:
            return_error('Failed to parse the provided timestamp.')

        # Get the current datetime
        now = datetime.now()

        # Calculate the difference in days
        delta = input_time - now
        days_difference = delta.days

        # Construct the output message based on the difference
        if days_difference > 0:
            message = f"The timestamp is **{days_difference}** day(s) in the future."
        elif days_difference < 0:
            message = f"The timestamp was **{abs(days_difference)}** day(s) ago."
        else:
            message = "The timestamp is **today**."

        # Return the result
        demisto.results({
            'Type': 1,
            'ContentsFormat': 'markdown',
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