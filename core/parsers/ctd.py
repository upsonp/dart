import ctd
import re
import pytz

from core import models


def read_ctd(ctd_file):
    if models.FileType(ctd_file.file_type) == models.FileType.btl:
        read_btl(ctd_file)


def read_btl(btl_file):
    models.Error.objects.filter(file=btl_file).delete()

    data_frame = ctd.from_btl(btl_file.file_path)
    mission = btl_file.directory.mission

    metadata = getattr(data_frame, "_metadata")
    header = metadata['header'].split('\n')

    event_number = None

    for h in header:
        # this is how the log file event and the bottle file are connected
        # sadly, it seems NFL region doesn't use an event number the same way ATL region does
        if 'event_number:' in h.lower():
            h_str = h.split(":")
            event_number = h_str[1].strip()

    event = models.Event.objects.get(mission=mission,
                                     instrument__instrument_type=models.InstrumentType.ctd.value,
                                     event_id=int(event_number))

    # we only want to use rows in the BTL file marked as 'avg'
    data_frame = data_frame[data_frame['Statistic'] == 'avg']

    col_headers = []
    for c in data_frame.columns:
        col_headers.append(c)

    # These are columns we either have no use for or we will specifically call and use later
    pop = ['Bottle', 'Bottle_', 'Date', 'Statistic', 'PrDM', 'Latitude', 'Longitude']
    for h in pop:
        try:
            b_idx = col_headers.index(h)
            col_headers.pop(b_idx)
        except ValueError:
            # if the label doesn't exists, which might happen in the case of 'Bottle_' a value error is raised
            pass

    sensors = {'added': [], 'models': []}
    for h in col_headers:
        # I've found that sensor columns usually have a naming convention where its xxx#yyy where the number denotes
        # the primary (0) sensor and the secondary (1) sensor. However, what follows the number is also relevant
        # to the sensor. Usually what follows the sensor priority denotes the unit. (i.e Sbeox0ML/L vs. Sbeox0V)
        c_name = re.split("(\d)", h, 1)

        priority = int(c_name[1]) + 1 if len(c_name) > 1 else None
        units = c_name[2].lower() if len(c_name) > 2 else None

        if h not in sensors['added']:
            sensor = models.Sensor.objects.filter(name=c_name[0])
            if priority:
                sensor = sensor.filter(priority=priority)

            if units:
                sensor = sensor.filter(units=units.lower())

            if len(sensor) <= 0:

                sen = models.Sensor(name=c_name[0])
                sen.sensor_type = models.get_sensor_type(c_name[0])

                if priority:
                    sen.priority = priority  # priorty in a sensor name starts counting at zero
                if units:
                    sen.units = units

                sensors['added'].append(h)
                sensors['models'].append(sen)

    models.Sensor.objects.bulk_create(sensors['models'])

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
            err = models.Error(mission=mission, file=btl_file, line=(metadata["skiprows"] + row[0]),
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
