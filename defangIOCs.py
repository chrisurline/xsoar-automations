# intended to be used as a transformer but is currently untested 

from typing import Dict, Any
import traceback
import re

def defang_ioc(ioc_type, ioc_value):
    if ioc_type == 'URL':
        # url
        defanged = re.sub(r'^http', 'hxxp', ioc_value)
        defanged = defanged.replace('.', '[.]')
    elif ioc_type == 'Domain':
        # domain
        defanged = ioc_value.replace('.', '[.]')
    elif ioc_type == 'Email':
        # email
        defanged = ioc_value.replace('@', '[@]').replace('.', '[.]')
    elif ioc_type == 'IP':
        # ip
        defanged = ioc_value.replace('.', '[.]')
    else:
        defanged = ioc_value  # if unknown type, return as is
    return defanged

def main():
    try:
        args = demisto.args()
        input_text = args.get('input_text', '')
        
        if not input_text:
            return_error('No input text provided.')

        # patterns to identify IOCs
        patterns = {
            'URL': re.compile(
                r'\b(?:http|https)://[^\s/$.?#].[^\s]*', re.IGNORECASE),
            'Email': re.compile(
                r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}\b', re.IGNORECASE),
            'IP': re.compile(
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'Domain': re.compile(
                r'\b(?:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b')
        }

        # replace IOCs with defanged versions
        def defang_text(text):
            defanged_text = text
            # track replacements to avoid overlapping issues
            replacements = []

            for ioc_type, pattern in patterns.items():
                for match in pattern.finditer(text):
                    ioc_value = match.group()
                    # skip if already defanged
                    if any(s in ioc_value for s in ['[.]', 'hxxp', '[@]']):
                        continue
                    # defang the IOC
                    defanged_ioc = defang_ioc(ioc_type, ioc_value)
                    # store the replacement
                    replacements.append((match.start(), match.end(), defanged_ioc))

            # sort replacements in reverse order to avoid index shifting
            replacements.sort(reverse=True)

            # perform the replacements
            for start, end, defanged_ioc in replacements:
                defanged_text = defanged_text[:start] + defanged_ioc + defanged_text[end:]

            return defanged_text

        result = defang_text(input_text)

        demisto.results(result)

    except Exception as e:
        return_error(f'Failed to execute script. Error: {str(e)}')

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
