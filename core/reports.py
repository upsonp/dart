import numpy as np

from core import models

from datetime import datetime
from os.path import join

from django.http import HttpResponse
from django.core.files.base import ContentFile

from . import utils

import csv


def send_report(report, file_name):
    string = ", ".join(report[0]) + "\n"

    for l in report[1]:
        string += ", ".join(l) + "\n"

    file_to_send = ContentFile(string)
    response = HttpResponse(file_to_send, content_type="text/csv")
    response['Content-Length'] = file_to_send.size
    response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'

    return response


def print_report(output_file_location, file_name, report):

    with open(join(output_file_location, file_name), mode="w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(report[0])
        for d in report[1]:
            csv_writer.writerow(d)


def generate_bottle_report(bottles, row_dic):
    headers = row_dic.keys()
    rows = []
    for b in bottles:
        row = []
        for k in headers:
            row.append(str(row_dic[k](b)))

        rows.append(row)

    return [headers, rows]


def generate_error_report(errors, row_dic):
    headers = row_dic.keys()
    rows = []
    for e in errors:
        row = []
        for k in headers:
            row.append(str(row_dic[k](e)))

        rows.append(row)

    return [headers, rows]


def generate_event_report(events, row_dic):
    headers = row_dic.keys()
    rows = []
    for e in events:
        row = []
        for k in headers:
            row.append(str(row_dic[k](e)))

        rows.append(row)

    return [headers, rows]


def get_variable_data(bottle, column_name):
    try:
        dc = models.get_variable_name(column_name)
    except models.Sensor.DoesNotExist as e:
        print(column_name)
        raise e

    bd = models.CTDData.objects.get(bottle=bottle, sensor=dc)
    return bd.value if bd else ""


def get_variable_type_data(bottle, sensor_type, priority=1, name=None, unit=None):
    bd = bottle.bottle_data.filter(sensor__sensor_details__sensor_type=sensor_type, sensor__priority=priority)

    if name:
        bd = bd.filter(sensor__column_name__istartswith=name)

    if unit:
        bd = bd.filter(sensor__sensor_details__units__iexact=unit)

    return bd[0].value if bd else ""


def get_salinity(b):
    salt_sample = models.SaltSample.objects.filter(bottle=b)
    return salt_sample[0].calculated_salinity if salt_sample else ""


def get_pressure(b: models.Bottle):
    return b.pressure


def get_mean_chl(b):
    chl_sample = models.ChlSample.objects.filter(bottle=b, sample_order=1)
    return chl_sample[0].mean_chl if chl_sample else ""


def get_mean_phae(b):
    chl_sample = models.ChlSample.objects.filter(bottle=b, sample_order=1)
    return chl_sample[0].mean_phae if chl_sample else ""


def get_oxygen_winkler(b, winkler):
    oxy_sample = models.OxygenSample.objects.filter(bottle=b)
    wink = ""
    if oxy_sample:
        if winkler == 1:
            return oxy_sample[0].winkler_1 if oxy_sample[0].winkler_1 else ""
        elif winkler == 2:
            return oxy_sample[0].winkler_2 if oxy_sample[0].winkler_2 else ""
    return ""


def get_oxygen_average(b):
    oxy_sample = models.OxygenSample.objects.filter(bottle=b)
    return oxy_sample[0].average if oxy_sample else ""


# called from the web browser to download a copy of the report
def report_elog_summary(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = get_elog_summary(mission=mission)

    file_name = f"{mission.name}_Elog_Summary.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_elog_summary(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = get_elog_summary(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Elog_Summary.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


# returns an array of two objects, element 0 is the header line, element 1 is the data
def get_elog_summary(mission):
    def get_elapsed_time(e):
        elapsed_time = 0
        try:
            next_event = models.Event.objects.get(mission=mission, event_id=e.event_id+1)
            elapsed_time = next_event.start_date-e.end_date
        except models.Event.DoesNotExist as e:
            # event doesn't exsit, carry on
            pass

        return elapsed_time

    def get_comments(e):
        comments = []
        for a in e.actions.all():
            if a.comment.strip() != "":
                comments.append(f"###{models.ActionType(a.action_type).label}###: {a.comment}")

        comments = " ".join(comments)

        return comments

    row_dic = {
        "Event": lambda e: e.event_id,
        "Station": lambda e: e.station.name,
        "INSTRUMENT": lambda e: e.instrument.name,
        "MIN_LAT": lambda e: e.start_location[0],
        "MIN_LON": lambda e: e.start_location[1],
        "MAX_LAT": lambda e: e.end_location[0],
        "MAX_LON": lambda e: e.end_location[1],
        "SDATE": lambda e: datetime.strftime(e.start_date, "%Y/%m/%d"),
        "STIME": lambda e: datetime.strftime(e.start_date, "%H:%M:%S"),
        "EDATE": lambda e: datetime.strftime(e.end_date, "%Y/%m/%d"),
        "ETIME": lambda e: datetime.strftime(e.end_date, "%H:%M:%S"),
        "Duration": lambda e: e.end_date-e.start_date,
        "NAME": lambda e: e.mission.name,
        "DESCRIPTOR": lambda e: "",
        "Elapsed_Time": lambda e: get_elapsed_time(e),
        "Comments": lambda e: get_comments(e)
    }

    events = mission.events.all().order_by("station__name")
    return generate_event_report(events=events, row_dic=row_dic)


# called from the web browser to download a copy of the report
def report_profile_summary(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = get_profile_summary(mission=mission)

    file_name = f"{mission.name}_Profile_Summary.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_profile_summary(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = get_profile_summary(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Profile_Summary.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def get_profile_summary(mission):

    def get_chl_voltage(bottle: models.Bottle):
        bd = bottle.bottle_data.filter(sensor__sensor_details__sensor_type=models.SensorType.fluorescence,
                                       sensor__priority=1, sensor__column_name__iexact="FlSP")

        return bd[0].value

    row_dic = {
        "Name": lambda b: b.event.mission.name,
        "Station": lambda b: b.event.station.name,
        "Event": lambda b: b.event.event_id,
        "Gear": lambda b: models.InstrumentType(b.event.instrument.instrument_type).label,
        "Sample": lambda b: b.bottle_id,
        "Chl_a_Holm-Hansen_F": lambda b: get_mean_chl(b),
        "Chl_Fluor_Voltage": lambda b: get_chl_voltage(b),
        "conductivity_CTD": lambda b: b.get_ctd_data(sensor_type=models.SensorType.conductivity, name='c'),
        "O2_CTD_mLL": lambda b: b.get_ctd_data(sensor_type=models.SensorType.oxygen, unit="ML/L"),
        "O2_Winkler_Auto": lambda b: get_oxygen_average(b),
        "PAR": lambda b: b.get_ctd_data(sensor_type=models.SensorType.par_logarithmic),
        "pH_CTD_nocal": lambda b: b.get_ctd_data(sensor_type=models.SensorType.ph),
        "Phaeo_Holm-HansenF": lambda b: get_mean_phae(b),
        "Pressure": lambda b: get_pressure(b),
        "Salinity_CTD": lambda b: b.get_ctd_data(sensor_type=models.SensorType.salinity),
        "Salinity_Sal_PSS": lambda b: get_salinity(b),
        "TE90": lambda b: b.get_ctd_data(sensor_type=models.SensorType.temperature, name='t'),
    }

    bottles = models.Bottle.objects.filter(event__mission=mission).order_by("event__station__name")
    return generate_bottle_report(bottles=bottles, row_dic=row_dic)


# called from the web browser to download a copy of the report
def report_biosum_report(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = get_biosum_report(mission=mission)

    file_name = f"{mission.name}_Auto_BioSum.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_biosum_report(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = get_biosum_report(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Auto_BioSum.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def get_biosum_report(mission):
    def get_ctd_index(b):
        events = [e.event_id for e in models.Event.objects.filter(instrument__instrument_type=
                                                                  models.InstrumentType.ctd.value).order_by("event_id")]
        return events.index(b.event.event_id) if b.event.event_id in events else -1


    row_dic = {
        "CTD": lambda b: get_ctd_index(b),
        "Event": lambda b: b.event.event_id,
        "STN": lambda b: b.event.station.name,
        "DATE_Z": lambda b: datetime.strftime(b.event.start_date, "%m/%d/%Y"),
        "DOY": lambda b: datetime.strftime(b.event.start_date, "%j"),
        "TIME_Z": lambda b: datetime.strftime(b.event.start_date, "%H%M"),
        "LAT_deg": lambda b: utils.convertDegs_DMS(b.event.start_location[0])[0],
        "LAT_min": lambda b: utils.convertDegs_DMS(b.event.start_location[0])[1],
        "LON_deg": lambda b: utils.convertDegs_DMS(b.event.start_location[1])[0],
        "LON_min": lambda b: utils.convertDegs_DMS(b.event.start_location[1])[1],
        "Lat_dec": lambda b: b.event.start_location[0],
        "Lon_dec": lambda b: b.event.start_location[1],
        "ID_TAG": lambda b: b.bottle_id,
        "CTD_Pressure": lambda b: b.pressure,
        "MEAN_CHL": lambda b: get_mean_chl(b),
        "MEAN_PHAEO": lambda b: get_mean_phae(b),
        "o2_(ml/l)": lambda b: get_oxygen_average(b),
        "Salinity_Sal_PSS": lambda b: get_salinity(b),
        "Salinity_CTD": lambda b: b.get_ctd_data(sensor_type=models.SensorType.salinity),
        "O2_CTD_mLL": lambda b: b.get_ctd_data(sensor_type=models.SensorType.oxygen, units='ML/L'),
        "Chl_Fluor_Voltage": lambda b: b.get_ctd_data(sensor_type=models.SensorType.fluorescence),
        "conductivity_CTD": lambda b: b.get_ctd_data(sensor_type=models.SensorType.conductivity, units='S/m'),
        "PAR": lambda b: b.get_ctd_data(sensor_type=models.SensorType.par_logarithmic),
        "pH_CTD_nocal": lambda b: b.get_ctd_data(sensor_type=models.SensorType.ph),
        "TE90": lambda b: b.get_ctd_data(sensor_type=models.SensorType.temperature),
        "TURW": lambda b: b.get_ctd_data(sensor_type=models.SensorType.turbidity)
    }

    bottles = models.Bottle.objects.filter(event__mission=mission).order_by("event__event_id")
    return generate_bottle_report(bottles=bottles, row_dic=row_dic)


# called from the web browser to download a copy of the report
def report_error_report(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = get_error_report(mission=mission)

    file_name = f"{mission.name}_Error_Report.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_error_report(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = get_error_report(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Error_Report.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def get_error_report(mission):

    row_dic = {
        "File": lambda e: e.file_name,
        "Line/Object": lambda e: e.line,
        "Error_Type": lambda e: models.ErrorType(e.error_code).label,
        "Message": lambda e: e.message,
        "Stack_Trace": lambda e: e.stack_trace
    }

    errors = models.Error.objects.filter(mission=mission)
    return generate_error_report(errors=errors, row_dic=row_dic)
