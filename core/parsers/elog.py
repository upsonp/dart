import io
import re

from datetime import datetime
from os.path import join

from core import models
from core.utils import convertDMS_degs


def set_attributes(obj, attr_key, attr):
    update = False
    if hasattr(obj, attr_key) and getattr(obj, attr_key) != attr:
        setattr(obj, attr_key, attr)
        update = True

    return update


def update_attributes(obj, attributes: dict, update_array: dict):
    update = False
    keys = attributes.keys()
    for attr_key in keys:
        if set_attributes(obj, attr_key, attributes[attr_key]):
            update = True
            update_array['fields'].add(attr_key)

    if update:
        update_array['objects'].append(obj)


def read_elog(log_file):
    errors = []

    print(f"Processing {log_file.file.name}")
    file = join(log_file.directory.directory, log_file.file.name)
    file_pointer = open(file=file, mode="r")
    stream = io.StringIO(file_pointer.read())

    # All mid objects start with $@MID@$ and end with a series of equal signs and a blank line.
    # Using regular expressions we'll split the whole stream in to mid objects, then process each object
    paragraph = re.split('====*\n\n', stream.read().strip())
    mid_map = {'file': log_file, 'buffer': {}}
    for mid in paragraph:
        # Each variable in a mid object starts with the label followed by a colon followed by the value
        tmp = re.findall('(.*?): *(.*?)\n', mid)

        # easily convert the (label, value) tuples into a dictionary
        buffer = dict(tmp)

        # pop off the mid object number used to reference this process if there is an issue processing the mid object
        mid_obj = buffer.pop('$@MID@$')

        # process the buffer creating the event objects
        mid_map['buffer'][mid_obj] = buffer

    mids = mid_map['buffer'].keys()

    mission = log_file.directory.mission

    models.Error.objects.filter(mission=mission, file_name=log_file.file.name).delete()
    elog_config = models.ElogConfig.get_default_elog_config(mission=mission)

    errors += process_stations_instruments(log_file, mid_map, mids, elog_config)
    errors += process_events(log_file, mid_map, mids, elog_config)
    errors += process_attachments_actions_time_location(log_file, mid_map, mids, elog_config)
    errors += process_variables(log_file, mid_map, mids, elog_config)

    file_pointer.close()

    models.Error.objects.bulk_create(errors)


def process_stations_instruments(log_file, mid_map, mids, elog_config):
    errors = []

    mission = log_file.directory.mission
    buff = mid_map['buffer']

    e_stations = [s.name for s in models.Station.objects.all()]
    e_instruments = [i.name for i in models.Instrument.objects.all()]

    stations = {'added': [], 'models': []}
    instruments = {'added': [], 'models': []}
    for m in mids:
        try:
            station = buff[m][elog_config.station.name]
            instrument = buff[m][elog_config.instrument.name]

            if station not in e_stations and station not in stations['added']:
                stations['added'].append(station)
                stations['models'].append(models.Station(name=station))

            if instrument not in e_instruments and instruments not in instruments['added']:
                try:
                    inst_type = models.InstrumentType[instrument.lower()].value
                except KeyError:
                    # if an unknown type is recieved consider this an 'other' event
                    inst_type = models.InstrumentType['other'].value

                instruments['added'].append(instrument)
                instruments['models'].append(models.Instrument(name=instrument, instrument_type=inst_type))
        except Exception as e:
            error = models.Error(mission=mission, file_name=log_file.file.name, line=m,
                                 message=f"Error processing stations and instruments for $@MID@$: "
                                         f"{m}", stack_trace=str(e))
            errors.append(error)

    models.Station.objects.bulk_create(stations['models'])
    models.Instrument.objects.bulk_create(instruments['models'])

    return errors


def process_events(log_file, mid_map, mids, elog_config):
    errors = []

    mission = log_file.directory.mission
    buf = mid_map['buffer']

    e_events = [e.event_id for e in models.Event.objects.filter(mission=mission)]

    p_events = []
    c_events = []
    u_events = {'objects': [], 'fields': set()}
    for m in mids:
        try:
            event_id = int(buf[m][elog_config.event.name])
            if event_id in p_events:
                # if an event has already been processed, don't process it again
                continue

            p_events.append(event_id)

            # we're done with these objects
            station_name = buf[m].pop(elog_config.station.name)
            instrument_name = buf[m].pop(elog_config.instrument.name)
            sample_id = buf[m].pop(elog_config.start_sample_id.name)
            sample_id = sample_id if sample_id != "" else None

            end_sample_id = buf[m].pop(elog_config.end_sample_id.name)
            end_sample_id = end_sample_id if end_sample_id != "" else None

            station = models.get_station(name=station_name)
            instrument = models.get_instrument(instrument_name=instrument_name)

            if event_id not in e_events:
                c_events.append(models.Event(mission=mission, event_id=event_id, station=station,
                                             instrument=instrument, sample_id=sample_id, end_sample_id=end_sample_id))
            else:
                attrs = {
                    'station': station,
                    'instrument': instrument,
                    'sample_id': sample_id,
                    'end_sample_id': end_sample_id
                }
                e = models.Event.objects.get(mission=mission, event_id=event_id)

                update_attributes(e, attrs, u_events)
        except Exception as e:
            error = models.Error(mission=mission, file_name=log_file.file.name, line=m,
                                 message=f"Error processing events for $@MID@$: "
                                         f"{m}", stack_trace=str(e))
            errors.append(error)

    models.Event.objects.bulk_create(c_events)
    if u_events['fields']:
        models.Event.objects.bulk_update(objs=u_events['objects'], fields=u_events['fields'])

    return errors


def get_action(event, event_type_label):
    if models.ActionType.has_value(event_type_label):
        return event.actions.get(action_type=models.ActionType.get(event_type_label))

    return event.actions.get(action_type=models.ActionType.other, action_type_other=event_type_label)


def process_attachments_actions_time_location(log_file, mid_map, mids, elog_config):
    errors = []

    mission = log_file.directory.mission
    buf = mid_map['buffer']

    instr_sensors = []
    c_actions = []
    u_actions = {'objects': [], 'fields': set()}
    cur_event = None
    time_position = None
    comment = None
    event_id = None
    evt_type_t = None
    event = None
    for m in mids:
        try:
            # This date is the date of the last elog update and isn't accurate for recording purpose
            buf[m].pop('Date')

            event_id = buf[m][elog_config.event.name]
            event = models.Event.objects.get(mission=mission, event_id=event_id)

            att_str = buf[m].pop(elog_config.attached.name)
            time_position = buf[m].pop(elog_config.time_position.name).split(" | ")
            comment = buf[m].pop(elog_config.comment.name)
            action_type_text = buf[m][elog_config.action.name]
            action_type = models.ActionType.get(action_type_text)

            if cur_event != event_id:
                atts = att_str.split(" | ")
                for a in atts:
                    if a.strip() != '':
                        if len(models.InstrumentSensor.objects.filter(event=event, name=a)) <= 0:
                            instr_sensors.append(models.InstrumentSensor(event=event, name=a))
        except Exception as e:
            error = models.Error(mission=mission, file=log_file.file.name, line=m,
                                 message=f"Error processing attachments for $@MID@$: {m}",
                                 stack_trace=str(e))
            errors.append(error)

        try:
            # this is a 'naive' date time with no time zone. But it should always be in UTC
            time_part = f"{time_position[1][0:2]}:{time_position[1][2:4]}:{time_position[1][4:6]}"
            date_time = datetime.strptime(f"{time_position[0]} {time_part} +00:00", '%Y-%m-%d %H:%M:%S %z')

            lat = convertDMS_degs(time_position[2])
            lon = convertDMS_degs(time_position[3])

            # if an event already contains this action, we'll update it
            if event.actions.filter(action_type=action_type).exists():
                action = get_action(event, action_type_text)

                attrs = {
                    'latitude': lat,
                    'longitude': lon,
                    'mid': m,
                    'comment': comment,
                }
                update_attributes(action, attrs, u_actions)

            else:
                action = models.Action(file=log_file, event=event,
                                       date_time=date_time, latitude=lat, longitude=lon,
                                       mid=m, action_type=action_type, comment=comment)
                if action_type == models.ActionType.other:
                    action.action_type_other = action_type_text

                c_actions.append(action)
        except models.Action.MultipleObjectsReturned as e:
            error = models.Error(mission=mission, file_name=log_file.file.name, line=m,
                                 error_code=models.ErrorType.duplicate_value,
                                 message=f"An event may not contain duplicate actions, Action may be misnamed for "
                                         f"$@MID@$: {m}", stack_trace=str(e))
            errors.append(error)
        except Exception as e:
            error = models.Error(mission=mission, file_name=log_file.file.name, line=m,
                                 message=f"Error processing actions for $@MID@$: "
                                         f"{m}", stack_trace=str(e))
            errors.append(error)

        cur_event = event_id

    models.InstrumentSensor.objects.bulk_create(instr_sensors)
    models.Action.objects.bulk_create(c_actions)
    if u_actions['fields']:
        models.Action.objects.bulk_update(objs=u_actions['objects'], fields=u_actions['fields'])

    return errors


def get_create_and_update_variables(action, buffer):
    variables_to_create = []
    variables_to_update = []
    for key, value in buffer.items():
        variable = models.get_variable_name(name=key)
        filtered_variables = models.VariableField.objects.filter(action=action, name=variable)
        if len(filtered_variables) <= 0:
            new_variable = models.VariableField(action=action, name=variable, value=value)
            variables_to_create.append(new_variable)
        else:
            update_variable = filtered_variables[0]
            update_variable.value = value
            variables_to_update.append(update_variable)

    return [variables_to_create, variables_to_update]


def process_variables(log_file, mid_map, mids, elog_config):
    errors = []

    mission = log_file.directory.mission
    buf = mid_map['buffer']

    fields_create = []
    fields_update = []
    for mid in mids:
        buffer = buf[mid]
        try:
            action = models.Action.objects.get(event__mission=mission, mid=mid)
            # models.get_variable_name(name=k) is going to be a bottle neck if a variable doesn't already exist
            variables_arrays = get_create_and_update_variables(action, buffer)
            fields_create += variables_arrays[0]
            fields_update += variables_arrays[1]
        except Exception as e:
            error = models.Error(mission=mission, file_name=log_file.file.name, line=mid,
                                 message=f"Error processing variables for $@MID@$: "
                                         f"{mid}", stack_trace=str(e))
            errors.append(error)

    models.VariableField.objects.bulk_create(fields_create)
    models.VariableField.objects.bulk_update(objs=fields_update, fields=['value'])

    return errors