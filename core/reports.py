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


def get_error_report(errors, row_dic):
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
        dc = models.get_data_column_name(column_name)
    except models.Sensor.DoesNotExist as e:
        print(column_name)
        raise e

    bd = models.BottleData.objects.get(bottle=bottle, column=dc)
    return bd.value if bd else ""


def get_variable_type_data(bottle, sensor_type, priority=1, name=None, unit=None):
    bd = models.BottleData.objects.filter(bottle=bottle, column__sensor_type=sensor_type, column__priority=priority)

    if name:
        bd = bd.filter(column__name__iexact=name)

    if unit:
        bd = bd.filter(column__units__iexact=unit)

    return bd[0].value if bd else ""


def get_salinity(b):
    salt_sample = models.SaltSample.objects.filter(bottle=b)
    return salt_sample[0].calculated_salinity if salt_sample else ""


def get_pressure(b):
    return get_variable_data(b, "PrDM")


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
    report = generate_elog_summary(mission=mission)

    file_name = f"{mission.name}_Elog_Summary.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_elog_summary(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = generate_elog_summary(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Elog_Summary.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


# returns an array of two objects, element 0 is the header line, element 1 is the data
def generate_elog_summary(mission):
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
    report = generate_profile_summary(mission=mission)

    file_name = f"{mission.name}_Profile_Summary.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_profile_summary(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = generate_profile_summary(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Profile_Summary.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def generate_profile_summary(mission):

    row_dic = {
        "Name": lambda b: b.event.mission.name,
        "Station": lambda b: b.event.station.name,
        "Event": lambda b: b.event.event_id,
        "Gear": lambda b: models.InstrumentType(b.event.instrument.instrument_type).label,
        "Sample": lambda b: b.bottle_id,
        "Total_Of_Value": lambda b: "IDK",
        "Chl_a_Holm-Hansen_F": lambda b: get_mean_chl(b),
        "Chl_Fluor_Voltage": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.chl.value),
        "conductivity_CTD": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.conductivity.value,
                                                             name='c'),
        "O2_CTD_mLL": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.oxygen, unit="v"),
        "O2_Winkler_Auto": lambda b: get_oxygen_average(b),
        "PAR": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.par.value),
        "pH_CTD_nocal": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.ph.value),
        "Phaeo_Holm-HansenF": lambda b: get_mean_phae(b),
        "Pressure": lambda b: get_pressure(b),
        "Salinity_CTD": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.salinity.value),
        "Salinity_Sal_PSS": lambda b: get_salinity(b),
        "TE90": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.temperature.value, name='t'),
        "TURW": lambda b: get_variable_type_data(bottle=b, sensor_type=models.SensorType.turw.value)
    }

    bottles = models.Bottle.objects.filter(event__mission=mission).order_by("event__station__name")
    return generate_bottle_report(bottles=bottles, row_dic=row_dic)


# called from the web browser to download a copy of the report
def report_salt_report(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = generate_salt_report(mission=mission)

    file_name = f"{mission.name}_Salt_Rpt.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_salt_report(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = generate_salt_report(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Salt_Rpt.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def generate_salt_report(mission):
    row_dic = {
        "Name": lambda b: b.event.mission.name,
        "Station": lambda b: b.event.station.name,
        "Event": lambda b: b.event.event_id,
        "Sample": lambda b: b.bottle_id,
        "Pressure": lambda b: get_pressure(b),
        "temp_ctd_p": lambda b: get_variable_data(b, "T090C"),
        "temp_ctd_s": lambda b: get_variable_data(b, "T190C"),
        "cond_ctd_p": lambda b: get_variable_data(b, "C0S/m"),
        "cond_ctd_s": lambda b: get_variable_data(b, "C1S/m"),
        "sal_ctd_p": lambda b: get_variable_data(b, "Sal00"),
        "sal_ctd_s": lambda b: get_variable_data(b, "Sal11"),
        "sal_rep1": lambda b: get_salinity(b),
        "sal_rep2": lambda b: ""
    }

    bottles = models.Bottle.objects.filter(event__mission=mission).order_by("event__event_id")
    return generate_bottle_report(bottles=bottles, row_dic=row_dic)


# called from the web browser to download a copy of the report
def report_oxy_report(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = generate_oxy_report(mission=mission)

    file_name = f"{mission.name}_Oxygen_Rpt.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_oxy_report(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = generate_oxy_report(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Oxygen_Rpt.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def generate_oxy_report(mission):
    row_dic = {
        "Name": lambda b: b.event.mission.name,
        "Station": lambda b: b.event.station.name,
        "Event": lambda b: b.event.event_id,
        "Sample": lambda b: b.bottle_id,
        "Pressure": lambda b: get_pressure(b),
        "oxy_ctd_p": lambda b: get_variable_data(b, "Sbeox0V"),
        "oxy_ctd_s": lambda b: get_variable_data(b, "Sbeox1V"),
        "oxy_w_rep1": lambda b: get_oxygen_winkler(b, 1),
        "oxy_w_rep2": lambda b: get_oxygen_winkler(b, 2)
    }

    bottles = models.Bottle.objects.filter(event__mission=mission).order_by("event__event_id")
    return generate_bottle_report(bottles=bottles, row_dic=row_dic)


# called from the web browser to download a copy of the report
def report_biosum_report(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = generate_biosum_report(mission=mission)

    file_name = f"{mission.name}_Auto_BioSum.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_biosum_report(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = generate_biosum_report(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Auto_BioSum.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def generate_biosum_report(mission):
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
        "CTD_Pressure": lambda b: get_pressure(b),
        "MEAN_CHL": lambda b: get_mean_chl(b),
        "MEAN_PHAEO": lambda b: get_mean_phae(b),
        "o2_(ml/l)": lambda b: get_oxygen_average(b),
        "Salinity_Sal_PSS": lambda b: get_salinity(b),
        "Salinity_CTD": lambda b: get_variable_data(b, 'Sal00'),
        "O2_CTD_mLL": lambda b: get_variable_data(b, 'Sbeox0ML/L'),
        "Chl_Fluor_Voltage": lambda b: get_variable_data(b, "FlECO-AFL"),
        "conductivity_CTD": lambda b: get_variable_data(b, "C0S/m"),
        "PAR": lambda b: get_variable_data(b, 'Par/log'),
        "pH_CTD_nocal": lambda b: get_variable_data(b, 'Ph'),
        "TE90": lambda b: get_variable_data(b, 'T090C'),
        "TURW": lambda b: get_variable_data(b, 'CStarAt0')
    }

    bottles = models.Bottle.objects.filter(event__mission=mission).order_by("event__event_id")
    return generate_bottle_report(bottles=bottles, row_dic=row_dic)


# called from the web browser to download a copy of the report
def report_error_report(request, pk):
    mission = models.Mission.objects.get(id=pk)
    report = generate_error_report(mission=mission)

    file_name = f"{mission.name}_Error_Report.csv"

    return send_report(report, file_name)


# callable from a django shell to create and save the report
def print_error_report(mission_id, output_file_location="./"):
    mission = models.Mission.objects.get(pk=mission_id)
    report = generate_error_report(mission=mission)

    # this probably should use the mission date
    file_name = f"{mission.name}_Error_Report.csv"

    print_report(output_file_location=output_file_location, file_name=file_name, report=report)


def generate_error_report(mission):

    row_dic = {
        "File": lambda e: e.file_name,
        "Line": lambda e: e.line,
        "Error_Type": lambda e: models.ErrorType(e.error_code).label,
        "Message": lambda e: e.message,
        "Stack_Trace": lambda e: e.stack_trace
    }

    errors = models.Error.objects.filter(mission=mission)
    return get_error_report(errors=errors, row_dic=row_dic)
