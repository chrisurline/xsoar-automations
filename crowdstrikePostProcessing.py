"""
crowdstrike post-processing script

this script closes associated CS falcon incidents or detections once the corresponding xsoar inc is closed

pre-reqs:
- incident field created:
    - field name: CrowdStrike Resolve Alert (crowdstrikeresolvealert)
    - single select (yes, no)
- field mapping to script
    - in xsoar, add the fields we need to the script arguments 
    - the script handles the basics: `crowdstrikeresolvealert`, `closeNotes` and `closeReason` 
    - add any other fields that are part of the 'Close Incident' pop-up
- tag script as 'post-processing' 

notes:
- confirms the resolve alert option is set to 'yes'
- this script will attempt to close both incidents and detections
- docker image used: demisto/python3:3.12.8.1983910
"""

from typing import Dict, Any
import traceback

def is_error(result):
    return result['Type'] == entryTypes['error']

def get_error(result):
    return result.get('Contents', '')

def get_crowdstrike_ids():

    incident_id = demisto.incident().get('Custom Fields', {}).get('alertid') or \
                  demisto.get(demisto.context(), 'CrowdStrike.Incident.id')
    detection_id = demisto.incident().get('Custom Fields', {}).get('alertid') or \
                  demisto.get(demisto.context(), 'CrowdStrike.Detection.id')
    
    # handle lists
    if isinstance(incident_id, list) and incident_id:
        incident_id = incident_id[0]

    if isinstance(detection_id, list) and detection_id:
        detection_id = detection_id[0]

    return incident_id, detection_id

def close_crowdstrike_incident(incident_id, close_code, xsoar_id, source_instance, status="Closed"):
    
    try:
        response = demisto.executeCommand(
            "cs-falcon-resolve-incident", {
                "ids": incident_id, 
                "status": status, 
                "tag": close_code, 
                "comment": "Closed by XSOAR automation [#${xsoar_id}]", 
                "using": source_instance
                }
        )
        if is_error(response[0]):
            demisto.error(f"Failed to close CrowdStrike Falcon incident {incident_id}: {get_error(response[0])}")
            return None
        else:
            demisto.info(f"Successfully closed CrowdStrike Falcon incident {incident_id} with status: {status}")
            return response[0].get('Contents')

    except Exception as e:
        demisto.error(f"Error closing CrowdStrike Falcon incident {incident_id}: {traceback.format_exc()}")
        return None

def close_crowdstrike_detection(detection_id, close_code, xsoar_id, source_instance, status="closed"):

    try:
        response = demisto.executeCommand(
            "cs-falcon-resolve-detection", {
                "ids": detection_id,
                "status": status,
                "tag": close_code,
                "comment": f"Closed by XSOAR automation [#${xsoar_id}]",
                "using": source_instance
            }
        )
        if is_error(response[0]):
            demisto.error(f"Failed to close CrowdStrike Falcon detection {detection_id}: {get_error(response[0])}")
            return None
        else:
            demisto.info(f"Successfully closed CrowdStrike Falcon detection {detection_id} with status: {status}")
            return response[0].get('Contents')
    
    except Exception as e:
        demisto.error(f"Error closing CrowdStrike Falcon detection {detection_id}: {traceback.format_exc()}")
        return None

def main():

    # get closure & incident details
    xsoar_id = demisto.incident.get('id')
    source_instance = demisto.incident.get('sourceInstance')
    close_reason = demisto.args().get('closeReason')
    close_notes = demisto.args().get('closeNotes')
    resolve_alert = demisto.args().get('crowdstrikeresolvealert')

    # map closure reason > crowdstrike tags
    close_code_map = {
        "False Positive": "false_positive",
        "True Positive": "true_positive",
        "Duplicate": ""
    }

    close_code = close_code_map.get(close_reason, "")

    try:
        if resolve_alert == "Yes":
            incident_id, detection_id = get_crowdstrike_ids()

            if incident_id:
                close_crowdstrike_incident(incident_id, close_code, xsoar_id, source_instance)

            if detection_id:
                close_crowdstrike_incident(detection_id, close_code, xsoar_id, source_instance)
        
        elif resolve_alert == "No":
            demisto.info("CrowdStrike Resolve Alert is set to no. Skipping CrowdStrike post processing.")
        else:
            demisto.info("CrowdStrike resolve Alert is not set or does not have a valid value. Skipping CrowdStrike post proccessing.")
    
    except Exception as e:
        demisto.error(f"An error occured in the CrowdStrike Falcon post processing script: {traceback.format_exc()}")
        demisto.results({
            'Type': entryTypes['error'],
            'ContentsFormat': formats['text'],
            'Contents': f"An error occurred in the CrowdStrike Falcon post processing script: {traceback.format_exc()}"
        })

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()