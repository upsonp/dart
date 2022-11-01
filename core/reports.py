from core import models

from datetime import datetime
from os.path import join

from django.http import HttpResponse
from django.core.files.base import ContentFile

import csv


def report_elog_summary(request, pk):
    mission = models.Mission.objects.get(id=pk)

    file_name = f"Elog_Summary_{mission.name}.csv"
    report = generate_elog_summary(pk)

    string = ", ".join(report[0]) + "\n"

    for l in report[1]:
        string += ", ".join(l) + "\n"

    file_to_send = ContentFile(string)
    response = HttpResponse(file_to_send, content_type="text/csv")
    response['Content-Length'] = file_to_send.size
    response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
    return response


def generate_elog_summary(mission_id):
    mission = models.Mission.objects.get(id=mission_id)
    # Event, Station, INSTRUMENT, MIN_LAT, MIN_LON, MAX_LAT, MAX_LON, SDATE, STIME, EDATE, ETIME, Duration,
    # NAME, DESCRIPTOR, Elapsed_Time, Comments

    events = mission.events.all()

    header = ["Event", "Station", "INSTRUMENT", "MIN_LAT", "MIN_LON", "MAX_LAT", "MAX_LON", "SDATE", "STIME", "EDATE",
              "ETIME", "Duration", "NAME", "DESCRIPTOR", "Elapsed_Time", "Comments"]
    rows = []
    for event in events:
        station = event.station.name
        instrument = event.instrument.name
        s_date = event.start_date
        e_date = event.end_date
        s_date_time = datetime.strftime(s_date, "%Y/%m/%d %H:%M:%S").split(" ")
        e_date_time = datetime.strftime(e_date, "%Y/%m/%d %H:%M:%S").split(" ")

        elapsed_time = 0
        try:
            next_event = models.Event.objects.get(mission=mission, event_id=event.event_id+1)
            elapsed_time = next_event.start_date-event.end_date
        except models.Event.DoesNotExist as e:
            # event doesn't exsit, carry on
            pass

        comments = []
        for a in event.actions.all():
            if a.comment.strip() != "":
                comments.append(f"###{models.ActionType(a.action_type).label}###: {a.comment}")

        comments = " ".join(comments)
        row = [
            str(event.event_id),
            str(station),
            str(instrument),
            str(event.start_location[0]),
            str(event.start_location[1]),
            str(event.end_location[0]),
            str(event.end_location[1]),
            str(s_date_time[0]),
            str(s_date_time[1]),
            str(e_date_time[0]),
            str(e_date_time[1]),
            str((e_date-s_date)),
            str(mission.name),
            str(''),  # description
            str(elapsed_time),  # elapsed time
            str(comments)]

        rows.append(row)

    return [header, rows]


def print_elog_summary(mission_id, output_file_location="./"):
    data = generate_elog_summary(mission_id=mission_id)

    mission = models.Mission.objects.get(pk=mission_id)

    # this probably should use the mission date
    file_name = f"Elog_Profile_Summary_{mission.name}_{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.csv"

    with open(join(output_file_location, file_name), mode="x", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(data[0])
        for d in data[1]:
            csv_writer.writerow(d)
