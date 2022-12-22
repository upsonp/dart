import ctd
import re

import pandas
import pytz

from core import models


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


def get_sensor_details(sensor_name: str) -> [models.SensorType, int, str]:
    """given a sensor name return [type, priority, UoM]"""
    sensor_name_parts = re.split("(\d)", sensor_name, 1)


def get_sensors(sensors: list) -> list:
    """give a list of sensor names return a list of sensors that need to be created"""


def get_ros_file(btl_file: models.DataFile) -> str:
    """given a CTD BTL file return the matching ROS file"""
    dir = btl_file.directory.directory
    file = btl_file.file.name[:-3] + "ROS"

    return dir + file


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


def create_sensors_from_ros_data(mission: models.Mission, exclude_sensors: list, ros_file: str) -> list:
    """given a ROS file create sensors objects from the config portion of the file"""

    summary = ctd.rosette_summary(ros_file)
    sensors = re.findall("# name \d+ = (.*?)\n", getattr(summary, '_metadata')['config'])

    existing_sensors = [sensor.column_name for sensor in mission.sensors.all()]
    mission_sensors = []
    for sensor in sensors:
        # [column_name]: [sensor_details]
        sensor_mapping = re.split(": ", sensor)
        if sensor_mapping[0] not in exclude_sensors and sensor_mapping[0] not in existing_sensors:
            sensor_type_string, priority, units, other = parse_sensor(sensor_mapping[1])
            sensor_type = models.SensorType.get(sensor_type_string)
            sensor_details = models.SensorDetails.objects.get_or_create(sensor_type=sensor_type,
                                                                        sensor_type_other=sensor_type_string,
                                                                        units=units, other=other)[0]
            new_mission_sensor = models.MissionSensor(mission=mission, column_name=sensor_mapping[0], priority=priority,
                                                      sensor_details=sensor_details)
            mission_sensors.append(new_mission_sensor)

    return mission_sensors


def read_btl(btl_file: models.DataFile):
    models.Error.objects.filter(file_name=btl_file.file.name).delete()

    data_frame = ctd.from_btl(btl_file.file_path)
    mission = btl_file.directory.mission

    event_number = get_event_number(data_frame=data_frame)

    event = models.Event.objects.get(mission=mission,
                                     instrument__instrument_type=models.InstrumentType.ctd.value,
                                     event_id=event_number)

    # These are columns we either have no use for or we will specifically call and use later
    pop = ['Bottle', 'Bottle_', 'Date', 'Statistic', 'PrDM', 'Latitude', 'Longitude']
    col_headers = get_sensor_names(data_frame=data_frame, exclude=pop)

    # we only want to use rows in the BTL file marked as 'avg' in the statistics column
    data_frame = data_frame[data_frame['Statistic'] == 'avg']

    exclude_sensors = ['scan', 'timeS', 'latitude', 'longitude', 'nbf', 'flag']
    ros_file = get_ros_file(btl_file=btl_file)
    new_sensors = create_sensors_from_ros_data(mission=mission, exclude_sensors=exclude_sensors, ros_file=ros_file)

    models.MissionSensor.objects.bulk_create(new_sensors)

    b_create = []
    b_update = {"data": [], "fields": []}
    bottle_date = data_frame[["Bottle", "Date", "PrDM"]]
    errors = []
    for row in bottle_date.iterrows():
        bottle_number = row[1]["Bottle"]
        bottle_id = bottle_number + event.sample_id - 1
        date = row[1]["Date"]
        pressure = row[1]["PrDM"]

        # assume UTC time if a timezone isn't set
        if not hasattr(date, 'timezone'):
            date = pytz.timezone("UTC").localize(date)

        if len(models.Bottle.objects.filter(event=event, bottle_number=bottle_number)) <= 0:
            models.Bottle.objects.filter(event=event, bottle_number=bottle_number).delete()

        if event.instrument.instrument_type == models.InstrumentType.ctd.value and bottle_id > event.end_sample_id:
            err = models.Error(mission=mission, file_name=btl_file.file.name, line=(metadata["skiprows"] + row[0]),
                               message=f"Warning: Bottle ID ({bottle_id}) for event {event.event_id} is outside the "
                                       f"ID range {event.sample_id} - {event.end_sample_id}",
                               stack_trace="",
                               error_code=models.ErrorType.bad_id)
            errors.append(err)

        if len(models.Bottle.objects.filter(event=event, bottle_number=bottle_number)) <= 0:
            b_create.append(models.Bottle(event=event, pressure=pressure, bottle_number=bottle_number,
                                          date_time=date, bottle_id=bottle_id))
        else:
            update = False
            b = models.Bottle.objects.get(event=event, bottle_number=bottle_number)

            if b.bottle_id != bottle_id:
                b.bottle_id = bottle_id
                if 'bottle_id' not in b_update['fields']:
                    b_update['fields'].append('date_time')
                update = True

            if b.date_time != date:
                b.date_time = date
                if 'date_time' not in b_update['fields']:
                    b_update['fields'].append('date_time')
                update = True

            if b.pressure != pressure:
                b.pressure = pressure
                if 'pressure' not in b_update['fields']:
                    b_update['fields'].append('pressure')
                update = True

            if update:
                b_update["data"].append(b)

    models.Error.objects.bulk_create(errors)
    models.Bottle.objects.bulk_create(b_create)
    if len(b_update['data']) > 0:
        models.Bottle.objects.bulk_update(objs=b_update['data'], fields=b_update['fields'])

    data_column_create = []
    data_column_update = []
    for c in col_headers:
        sensor = models.get_sensor_name(c)

        df = data_frame[["Bottle", c]]
        for data in df.iterrows():
            bottle = models.Bottle.objects.get(event=event, bottle_number=data[1]["Bottle"])
            b_data = bottle.bottle_data.all()
            if b_data.filter(sensor=sensor):
                ctd_update = b_data.get(sensor=sensor)
                if ctd_update.value != data[1][c]:
                    ctd_update.value = data[1][c]
                    data_column_update.append(ctd_update)
            else:
                data_column_create.append(models.CTDData(bottle=bottle, sensor=sensor, value=data[1][c]))

    models.CTDData.objects.bulk_create(data_column_create)
    models.CTDData.objects.bulk_update(data_column_update, fields=["value"])
