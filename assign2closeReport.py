import demistomock as demisto
from CommonServerPython import *
import dateparser

def main():
    # You can supply 'incidentQuery' via script arguments, or just hard-code your desired query below.
    query = demisto.args().get("incidentQuery", "status:Closed")

    # 1) Retrieve closed incidents based on 'incidentQuery'
    res = demisto.executeCommand("getIncidents", {"query": query, "size": 1000})
    if isError(res[0]):
        return_error("Failed to get incidents: " + get_error(res[0]))

    incidents_data = res[0].get("Contents", {}).get("data", [])
    if not incidents_data:
        return_results("No closed incidents found with the given query.")
        return

    # Dictionary to sum total minutes between AssignToMe and Close, keyed by user
    user_time_deltas = {}

    # 2) For each incident, retrieve war-room entries and find times
    for inc in incidents_data:
        inc_id = inc.get("id")
        # Optional: incident owner if you'd rather group by owner
        # inc_owner = inc.get("owner", "Unassigned")

        # If the incident doesn't have a close time, skip it
        close_time_str = inc.get("closed")
        if not close_time_str:
            continue
        try:
            close_time = dateparser.parse(close_time_str)
        except Exception as e:
            demisto.error(f"Could not parse close time for incident {inc_id}: {e}")
            continue
        if not close_time:
            continue

        # Pull War Room entries for this incident
        entries_res = demisto.executeCommand("getEntries", {"id": inc_id})
        if isError(entries_res[0]):
            demisto.error(f"Failed to get entries for incident {inc_id}: {get_error(entries_res[0])}")
            continue
        entries = entries_res[0].get("Contents", [])

        # Find the first time "AssignToMe" was run
        assign_time = None
        user = "Unknown"

        for e in entries:
            # Type=4 often indicates system or investigation log entries
            # Adjust if your environment logs the command differently.
            if e.get("Type") == 4 and "AssignToMe" in e.get("Contents", ""):
                assign_time_str = e.get("When")
                user = e.get("User", "Unknown")
                try:
                    assign_time = dateparser.parse(assign_time_str)
                except Exception as e2:
                    demisto.error(f"Could not parse assign time for incident {inc_id}: {e2}")
                    continue

                # Once the first AssignToMe is found, break
                if assign_time:
                    break

        if not assign_time:
            # This incident doesn't have an AssignToMe record in the war room
            continue

        # 3) Calculate time difference (in minutes) between AssignToMe and incident close
        delta = close_time - assign_time
        delta_minutes = delta.total_seconds() / 60.0

        # 4) Sum the time by war-room user (change to inc_owner if you prefer grouping by incident owner)
        user_time_deltas[user] = user_time_deltas.get(user, 0) + delta_minutes

    # 5) Prepare data for a bar chart
    # XSOAR custom charts generally expect a list of {name: <str>, data: <numeric>}
    data_for_bar = []
    for usr, total_minutes in user_time_deltas.items():
        data_for_bar.append({"name": usr, "data": round(total_minutes, 2)})

    # If no data was collected, return an informational message instead
    if not data_for_bar:
        return_results("No matching AssignToMe vs. Close data found in the given incidents.")
        return

    # Return the data in a format recognized by XSOAR for bar charts.
    return_results({
        "Type": 17,  # Chart type in XSOAR
        "ContentsFormat": formats["json"],
        "Contents": data_for_bar
    })

if __name__ in ("__main__", "__builtin__", "builtins"):
    main()