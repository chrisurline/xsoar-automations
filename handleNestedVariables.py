# created to handle resolving nested variables in email templates that are stored in JSON format
# should be able to handle any type of string - but untested

from typing import Dict, Any
import traceback
import json
import re

def process_string(s):
    pattern = r'\$\{(.*?)\}'
    matches = re.findall(pattern, s)
    for match in matches:
        # Retrieve the value from the context using the placeholder
        context_value = demisto.get(demisto.context(), match)
        if context_value is None:
            context_value = ''
        # Replace the placeholder with the actual value
        s = s.replace('${' + match + '}', str(context_value))
    return s

def process_json(obj):
    if isinstance(obj, dict):
        return {k: process_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [process_json(elem) for elem in obj]
    elif isinstance(obj, str):
        return process_string(obj)
    else:
        return obj

def main():
    try:
        # get args
        input_json_str = demisto.args().get('json_object')
        input_json = json.loads(input_json_str)

        # process data
        output_json = process_json(input_json)

        # return in json format
        demisto.results({
            'Type': entryTypes['note'],
            'ContentsFormat': formats['json'],
            'Contents': output_json,
            'EntryContext': {'ProcessedJSON': output_json}
        })
    except Exception as e:
        return_error(f'Failed to execute the script. Error: {str(e)}')

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
