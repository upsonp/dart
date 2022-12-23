import ctd
import re
import os

import pandas
import pytz

from core import models

from core import validations


def read_ctd(ctd_file):
    if models.FileType(ctd_file.file_type) == models.FileType.btl:
        read_btl(ctd_file)


def get_event_number(data_frame: pandas.DataFrame) -> int:
    """retrieve the elog event number this bottle file is attached to"""

    # when a bottle file is read using the ctd package the top part of the file is saved in the _metadata
    metadata = getattr(data_frame, "_metadata")

    # for the Atlantic Region the last three digits of the bottle file name contains the elog event number
    event_number = metadata['name'][-3:]
    return int(event_number)


def get_sensor_names(data_frame: pandas.DataFrame, exclude: list = []) -> list:
    """given a dataframe and a list of columns to exclude, return the remaining column that represent sensors"""

    return [instrument for instrument in data_frame.columns if instrument not in exclude]


def get_sensors(sensors: list) -> list:
    """give a list of sensor names return a list of sensors that need to be created"""


def get_ros_file(btl_file: models.DataFile) -> str:
    """given a CTD BTL file return the matching ROS file"""
    dir = btl_file.directory.directory
    file = btl_file.file.name[:-3] + "ROS"

    return os.path.join(dir, file)


def _get_units(sensor_description: str) -> [str, str]:
    """given a sensor description, find, remove and return the uom and remaining string"""
    uom_pattern = " \\[(.*?)\\]"
    uom = re.findall(uom_pattern, sensor_description)
    uom = uom[0] if uom else ""
    return uom, re.sub(uom_pattern, "", sensor_description)


def _get_priority(sensor_description: str) -> [int, str]:
    """given a sensor description, with units removed, find, remove and return the priority and remaining string"""
    priority_pattern = ", (\d)"
    priority = re.findall(priority_pattern, sensor_description)
    priority = priority[0] if priority else 1
    return int(priority), re.sub(priority_pattern, "", sensor_description)


def _get_sensor_type(sensor_description: str) -> [str, str]:
    """given a sensor description with priority and units removed return the sensor type and remaining string"""
    remainder = sensor_description.split(", ")
    # if the sensor type wasn't in the remaining comma seperated list then it is the first value of the description
    return remainder[0], ", ".join([remainder[i] for i in range(1, len(remainder)) if len(remainder) > 1])


def parse_sensor(sensor: str) -> [str, int, str, str]:
    """given a sensor description parse out the type, priority and units returning """
    units, sensor_a = _get_units(sensor)
    priority, sensor_b = _get_priority(sensor_a)
    sensor_type, remainder = _get_sensor_type(sensor_b)

    return sensor_type, priority, units, remainder


def get_new_sensors_from_ros_data(mission: models.Mission, exclude_sensors: list, ros_file: str) -> list:
    """given a ROS file create sensors objects from the config portion of the file"""

    summary = ctd.rosette_summary(ros_file)
    sensors = re.findall("# name \d+ = (.*?)\n", getattr(summary, '_metadata')['config'])

    excluding_sensors = [sensor.column_name.lower() for sensor in mission.sensors.all()] + \
                        [exclude.lower() for exclude in exclude_sensors]
    mission_sensors = []
    for sensor in sensors:
        # [column_name]: [sensor_details]
        sensor_mapping = re.split(": ", sensor)

        # make sure the first letter of the column name is capitalized
        column_name = sensor_mapping[0]
        column_name = column_name[0].upper() + column_name[1:]

        if column_name.lower() in excluding_sensors:
            continue

        sensor_type_string, priority, units, other = parse_sensor(sensor_mapping[1])
        sensor_type = models.SensorType.get(sensor_type_string)
        sensor_details = models.SensorDetails.objects.get_or_create(sensor_type=sensor_type,
                                                                    sensor_type_other=sensor_type_string,
                                                                    units=units, other=other)[0]

        new_mission_sensor = models.MissionSensor(mission=mission, column_name=column_name,
                                                  priority=priority, sensor_details=sensor_details)
        mission_sensors.append(new_mission_sensor)

    return mission_sensors


def parse_sensor_name(sensor: str) -> [models.SensorType, int, str]:
    """Given a sensor name, return the type of sensor, its priority and units where available"""
    # For common sensors the common format for the names is [sensor_type][priority][units]
    # Sbeox0ML/L -> Sbeox (Sea-bird oxygen), 0 (primary sensor), ML/L
    # many sensors follow this format, the ones that don't are likely located, in greater detail, in
    # the ROS file configuration
    details = re.match("([A-Z][a-z]*)(\d{0,1})([A-Z]*.*)", sensor).groups()
    if not details:
        raise Exception(f"Sensor '{sensor}' does not follow the expected naming convention")

    sensor_type = models.get_sensor_type(details[0])
    priority = int(details[1] if len(details[1]) > 1 else 0) + 1  # priority 0 means primary sensor, 1 means secondary
    units = details[2] if len(details) > 2 else None

    return [sensor_type, priority, units]


def get_new_sensors_from_sensor_name(mission: models.Mission, sensors: list[str]) -> list[models.MissionSensor]:
    """Given a list of sensor names, or 'column headings', create a list of mission sensors that don't already exist"""
    mission_sensors = []
    existing_sensors = [sensor.column_name for sensor in mission.sensors.all()]
    for sensor in sensors:
        if sensor in existing_sensors:
            continue

        details = parse_sensor_name(sensor)

        sensor_details = models.SensorDetails.objects.get_or_create(sensor_type=details[0],
                                                                    sensor_type_other=sensor,
                                                                    units=details[2], other=sensor)[0]

        new_mission_sensor = models.MissionSensor(mission=mission, column_name=sensor,
                                                  priority=details[1], sensor_details=sensor_details)
        mission_sensors.append(new_mission_sensor)

    return mission_sensors


def process_sensors(btl_file: models.DataFile, column_headers: list[str], exclude_sensors: list[str]):
    """Given a Data File and a list of column, MissionSensors will be created if they do not already exist or aren't
    part of a set of excluded sensors"""
    mission = btl_file.directory.mission

    ros_file = get_ros_file(btl_file=btl_file)
    new_sensors = get_new_sensors_from_ros_data(mission=mission, exclude_sensors=exclude_sensors, ros_file=ros_file)
    models.MissionSensor.objects.bulk_create(new_sensors)

    # The ROS file gives us all kinds of information about special sensors that are commonly added and removed from the
    # CTD, but it does not cover sensors that are normally on the CTD by default.
    created_sensors = [sensor.column_name for sensor in mission.sensors.all()]
    default_sensors = [column for column in column_headers if column not in created_sensors]
    new_sensors = get_new_sensors_from_sensor_name(mission=mission, sensors=default_sensors)
    models.MissionSensor.objects.bulk_create(new_sensors)


def update_field(obj, field_name: str, value) -> bool:
    if not hasattr(obj, field_name):
        return False
    if getattr(obj, field_name) == value:
        return False

    setattr(obj, field_name, value)
    return True


def update_bottle(bottle: models.Bottle, check_fields: dict[str, object]) -> set:
    """Given a bottle and a dictionary of field name and 'new' value, check if a bottles attributes need to be updated
    return a set of fields that changed if an update was required."""
    fields = set()
    for field in check_fields:
        if update_field(bottle, field, check_fields[field]):
            fields.add(field)

    return fields


def process_bottles(file_name: str, event: models.Event, data_frame: pandas.DataFrame):
    skipped_rows = getattr(data_frame, "_metadata")["skiprows"]

    # we only want to use rows in the BTL file marked as 'avg' in the statistics column
    data_frame_avg = data_frame[data_frame['Statistic'] == 'avg']

    b_create = []
    b_update = {"data": [], "fields": set()}
    bottle_data = data_frame_avg[["Bottle", "Date", "PrDM"]]
    errors = []
    for row in bottle_data.iterrows():
        line = skipped_rows + row[0] + 1
        bottle_number = row[1]["Bottle"]
        bottle_id = bottle_number + event.sample_id - 1
        date = row[1]["Date"]
        pressure = row[1]["PrDM"]

        # assume UTC time if a timezone isn't set
        if not hasattr(date, 'timezone'):
            date = pytz.timezone("UTC").localize(date)

        errors += validations.validate_bottle_sample_range(file=file_name, event=event, bottle_id=bottle_id, line=line)

        if models.Bottle.objects.filter(event=event, bottle_number=bottle_number).exists():
            b = models.Bottle.objects.get(event=event, bottle_number=bottle_number)

            check_fields = {'bottle_id': bottle_id, 'date_time': date, 'pressure': pressure}
            updated_fields = update_bottle(b, check_fields)
            if len(updated_fields) > 0:
                b_update['data'].append(b)
                b_update['fields'] = b_update['fields'].union(updated_fields)
            continue

        new_bottle = models.Bottle(event=event, pressure=pressure, bottle_number=bottle_number, date_time=date,
                                   bottle_id=bottle_id)
        b_create.append(new_bottle)

    models.Error.objects.bulk_create(errors)
    models.Bottle.objects.bulk_create(b_create)
    if len(b_update['data']) > 0:
        models.Bottle.objects.bulk_update(objs=b_update['data'], fields=b_update['fields'])


def process_data(event: models.Event, data_frame: pandas.DataFrame, column_headers: list[str]):
    mission = event.mission

    # we only want to use rows in the BTL file marked as 'avg' in the statistics column
    data_frame_avg = data_frame[data_frame['Statistic'] == 'avg']
    data_frame_avg._metadata = data_frame._metadata

    data_column_create = []
    data_column_update = []
    for column_name in column_headers:
        sensor = models.MissionSensor.objects.get(mission=mission, column_name=column_name)

        df = data_frame_avg[["Bottle", column_name]]
        for data in df.iterrows():
            bottle = models.Bottle.objects.get(event=event, bottle_number=data[1]["Bottle"])
            b_data = bottle.bottle_data.all()
            if b_data.filter(sensor__column_name=sensor.column_name):
                ctd_update = b_data.get(sensor=sensor)
                if ctd_update.value != data[1][column_name]:
                    ctd_update.value = data[1][column_name]
                    data_column_update.append(ctd_update)
            else:
                data_column_create.append(models.CTDData(bottle=bottle, sensor=sensor, value=data[1][column_name]))

    models.CTDData.objects.bulk_create(data_column_create)
    models.CTDData.objects.bulk_update(data_column_update, fields=["value"])


def read_btl(btl_file: models.DataFile):
    models.Error.objects.filter(file_name=btl_file.file.name).delete()

    data_frame = ctd.from_btl(btl_file.file_path)
    mission = btl_file.directory.mission

    event_number = get_event_number(data_frame=data_frame)

    event = models.Event.objects.get(mission=mission,
                                     instrument__instrument_type=models.InstrumentType.ctd.value,
                                     event_id=event_number)

    # These are columns we either have no use for or we will specifically call and use later
    pop = ['Bottle', 'Bottle_', 'Date', 'Scan', 'TimeS', 'Statistic', 'Latitude', 'Longitude']
    col_headers = get_sensor_names(data_frame=data_frame, exclude=pop)

    exclude_sensors = ['scan', 'timeS', 'latitude', 'longitude', 'nbf', 'flag']
    process_sensors(btl_file=btl_file, column_headers=col_headers, exclude_sensors=exclude_sensors)
    process_bottles(file_name=btl_file.file.name, event=event, data_frame=data_frame)
    process_data(event=event, data_frame=data_frame, column_headers=col_headers)


