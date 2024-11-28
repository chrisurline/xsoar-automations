from typing import Dict, Any
import traceback
import re

def refang_ioc(ioc_value):
    # refang common defanged patterns
    ioc_value = ioc_value.replace('hxxp', 'http')
    ioc_value = ioc_value.replace('hxxps', 'https')
    ioc_value = ioc_value.replace('[.]', '.')
    ioc_value = ioc_value.replace('[@]', '@')
    return ioc_value

def main():
    try:
        args = demisto.args()
        input_text = args.get('input_text', '')
        
        if not input_text:
            return_error('No input text provided.')

        # patterns to identify defanged IOCs
        patterns = {
            'Defanged_URL': re.compile(
                r'\b(?:hxxp|hxxps)://[^\s/$.?#].[^\s]*', re.IGNORECASE),
            'Defanged_Email': re.compile(
                r'\b[a-zA-Z0-9._%+\[\]-]+@\[[^\s]+\]', re.IGNORECASE),
            'Defanged_IP': re.compile(
                r'\b(?:[0-9]{1,3}\[\.\]){3}[0-9]{1,3}\b'),
            'Defanged_Domain': re.compile(
                r'\b(?:[a-zA-Z0-9.-]+\[\.\][a-zA-Z]{2,})\b')
        }

        # replace defanged IOCs with refanged versions
        def refang_text(text):
            refanged_text = text
            # keep track of replacements to avoid overlapping issues
            replacements = []

            for pattern in patterns.values():
                for match in pattern.finditer(text):
                    ioc_value = match.group()
                    # Refang the IOC
                    refanged_ioc = refang_ioc(ioc_value)
                    # Store the replacement
                    replacements.append((match.start(), match.end(), refanged_ioc))

            # sort replacements in reverse order to avoid index shifting
            replacements.sort(reverse=True)

            # perform the replacements
            for start, end, refanged_ioc in replacements:
                refanged_text = refanged_text[:start] + refanged_ioc + refanged_text[end:]

            return refanged_text

        result = refang_text(input_text)

        demisto.results(result)

    except Exception as e:
        return_error(f'Failed to execute script. Error: {str(e)}')

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
