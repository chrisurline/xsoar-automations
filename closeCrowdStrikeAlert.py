"""
crowdstrike post-processing script

this script closes associated CS falcon incidents or detections after an xsoar inc is closed.

pre-reqs:
- incident field created:
    - single select (yes, no)
    - field name: CrowdStrike Resolve Alert (crowdstrikeresolvealert)

notes:
- confirms the xsoar incident is closed
- confirms the resolve alert option is set to 'yes'
- this script will attempt to close both incidents and detections
"""

import demistomark as dm
import traceback

def is_error(result):
    return result['Type'] == entryTypes['error']

def get_error(result):
    return result.get('Contents', '')

def get_crowdstrike_ids():

  incident_id = demisto.incident().get('CustomFields', {}).get('crowdstrikefalconincidentid') or \
                demisto.get(demisto.context(), 'CrowdStrike.Incident.id')
  detection_id = demisto.incident().get('CustomFields', {}).get('crowdstrikefalcondetectionid') or \
                 demisto.get(demisto.context(), 'CrowdStrike.Detection.id')

  #Handle Lists
  if isinstance(incident_id, list) and incident_id:
      incident_id = incident_id[0]

  if isinstance(detection_id, list) and detection_id:
      detection_id = detection_id[0]

  return incident_id, detection_id

def close_crowdstrike_incident(incident_id, xsoar_id, status="Closed"):

  try:
    response = demisto.executeCommand(
        "cs-falcon-resolve-incident", {"incident_id": incident_id, "status": status, "comment": f"Closed by XSOAR automation [#{xsoar_id}]"}
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

def close_crowdstrike_detection(detection_id, xsoar_id, status="closed"):

  try:
    response = demisto.executeCommand(
        "cs-falcon-resolve-detection", {"detection_id": detection_id, "status": status, "comment": f"Closed by XSOAR automation [#{xsoar_id}]"}
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
  
  xsoar_id = demisto.incident().get('id')

  try:
    # Only execute if the incident status is 'Closed'
    if demisto.incident().get('status') == 2: # 2 represents 'Closed' in XSOAR incident status
      incident_id, detection_id = get_crowdstrike_ids()

      if incident_id:
        close_crowdstrike_incident(incident_id, xsoar_id)

      if detection_id:
        close_crowdstrike_detection(detection_id, xsoar_id)
    else:
        demisto.info(f"Incident status is not Closed. Current status: {demisto.incident().get('status')}. Skipping CrowdStrike post processing.")

  except Exception as e:
    demisto.error(f"An error occurred in the CrowdStrike Falcon post processing script: {traceback.format_exc()}")
    demisto.results({
        'Type': entryTypes['error'],
        'ContentsFormat': formats['text'],
        'Contents': f"An error occurred in the CrowdStrike Falcon post processing script: {traceback.format_exc()}"
    })

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()