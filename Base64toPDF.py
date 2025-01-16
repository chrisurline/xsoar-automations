# thrown together for PAN WildFire Reports integration
# the xsoar threat intel module should include a license for this integration - may need to ask your rep
# config args: `input` + `output_filename` - both required, add default value for filename
# when running the '!internal-wildfire-get-report', it doesn't output to context by default so use 'extend-context'

from typing import Dict, Any
import traceback
import base64

def base64_to_pdf(base64_string, output_file):

    decoded_file = base64.b64decode(base64_string)

    return fileResult(output_file, decoded_file)

def main():
    try:
        base64_string = demisto.args().get('input')
        output_file = demisto.args().get('output_filename')

        return_results(base64_to_pdf(base64_string, output_file))
    except Exception as ex:
        demisto.error(traceback.format_exc()) # print the traceback
        return_error(f'Failed to execute Base64 to PDF script. Error: {str(ex)}')

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()