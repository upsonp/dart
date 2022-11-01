import os
import threading
import time

import ctd
import io
import pytz

from openpyxl import load_workbook

from timeit import default_timer as timer

from datetime import datetime
from os.path import join, isfile

from django.http import JsonResponse

from core import models
from threading import Lock

processing = []


def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


def convertDMS_degs(dms_string):
    dms = dms_string.split()
    nsew = dms[2].upper()  # north, south, east, west
    degs = (float(dms[0]) + float(dms[1]) / 60) * (-1 if (nsew == 'S' or nsew == 'W') else 1)

    return degs


def get_files(request):
    type = models.FileType[request.GET['file_type'].lower()] if 'file_type' in request.GET else None
    mission = request.GET['mission_id'] if 'mission_id' in request.GET else None

    files = []
    log_dir = models.DataFileDirectory.objects.get(mission_id=mission, file_types__file_type=type.value)
    for path in os.listdir(log_dir.directory):
        if os.path.isfile(join(log_dir.directory, path)) and path.lower().endswith(type.label.lower()):
            if len(log_dir.data_files.filter(file=path)) <= 0:
                files.append(models.DataFile(directory=log_dir, file_type=type.value, file=path, processed=False))

    models.DataFile.objects.bulk_create(files)

    return JsonResponse({'files': [{'fid': f.pk, 'file_name': f.file.name, 'processed': f.processed} for f in
                                   models.DataFile.objects.filter(directory=log_dir)]})


def get_ctd_files(request):
    btl_files = []
    mission_id = request.GET['mission_id']
    if 'fid' in request.GET:

        fid = request.GET["fid"]

        btl_dir = models.DataFileDirectory.objects.get(mission_id=mission_id,
                                                       file_types__file_type=models.FileType.btl.value)
        btl_file = btl_dir.data_files.get(pk=fid)
        btl_file.log_errors.all().delete()

        read_ctd(btl_file)
        btl_files.append(btl_file)
        post_validation(btl_file)

        errors = models.LogError.objects.filter(file=btl_file)
        if len(errors) > 0:
            return JsonResponse({'errors': [{"pk": e.pk, "line": e.line, "msg": e.message, "trace": e.stack_trace}
                                            for e in errors]})
        else:
            btl_file.processed = True
            btl_file.save()

    return JsonResponse({'action': 'updated'})


def process_elog(request):
    log_files = []
    mission_id = request.GET['mission_id']
    if 'fid' in request.GET:

        fid = request.GET["fid"]

        log_dir = models.DataFileDirectory.objects.get(mission_id=mission_id,
                                                       file_types__file_type=models.FileType.log.value)
        log_file = log_dir.data_files.get(pk=fid)
        log_file.log_errors.all().delete()

        events = models.Event.objects.filter(actions__in=log_file.actions.all()).distinct()
        events.delete()

        read_elog(log_file)
        log_files.append(log_file)
        post_validation(log_files)

        errors = models.LogError.objects.filter(file=log_file)
        if len(errors) > 0:
            return JsonResponse({'errors': [{"pk": e.pk, "line": e.line, "msg": e.message, "trace": e.stack_trace}
                                            for e in errors]})
        else:
            log_file.processed = True
            log_file.save()

    return JsonResponse({'action': 'updated'})


def post_validation(log_files):
    pass


def read_elog(log_file):
    print(f"Processing {log_file.file.name}")
    file = join(log_file.directory.directory, log_file.file.name)
    stream = io.StringIO(open(file=file, mode="r").read())

    buffer = dict()

    lines_read = 0
    data_read = 0  # this is the number of bytes read as opposed to the number of lines read
    mid_obj = None
    start_time = timer()
    for line in stream:
        lines_read += 1
        data_read += len(line)
        s_line = str(line).strip()

        # skip blank lines and lines that start with '='
        if s_line == '' or s_line.startswith("="):
            continue

        # when you find a $@MID@$ label this is the beginning of a new object
        if s_line.startswith("$@MID@$"):

            if mid_obj:
                # We've found a new tag, dump the current data, if there is any, and load it to the database
                _load_buffer(log_file, buffer, mid_obj)

                buffer.clear()
                print(f"buffer: {(timer()-start_time)}")
                start_time=timer()

            # for error recording what object were we reading and what line did it start on
            mid_obj = s_line[8:].strip()
        else:
            # buffer the new line until we reach the end of the file or a new $@MID@$ tag
            var = s_line.split(":", 1)
            buffer[var[0].strip()] = var[1].strip() if len(var) > 1 else ""
    else:
        if mid_obj:
            # We've found a new tag, dump the current data, if there is any, and load it to the database
            _load_buffer(log_file, buffer, mid_obj)

    print("Done")


def _load_buffer(log_file, buffer, mid_obj):
    time_start = timer()

    mission = log_file.directory.mission
    try:
        if len(buffer.items()) > 0:
            event = buffer.pop("Event")

            # This date is the date of the last elog update and isn't accurate for recording purpose
            buffer.pop('Date')

            time_position = buffer.pop("Time|Position").split(" | ")

            station_name = buffer.pop('Station')
            instrument = buffer.pop('Instrument')

            sample_id = buffer.pop('Sample ID').strip()
            end_sample_id = buffer.pop('End_Sample_ID').strip()

            time_var = timer()
            print(f'vars: {(time_var-time_start)}')
            if len(models.Event.objects.filter(mission=mission, event_id=event)) <= 0:
                sdb = models.get_station(name=station_name)

                event = models.Event(mission=mission, event_id=event, station=sdb,
                                     sample_id=sample_id if sample_id != "" else None,
                                     end_sample_id=end_sample_id if end_sample_id != "" else None)
                event.save()

                time_event = timer()
                print(f'Event: {(time_event-time_var)}')
                try:
                    inst_type = models.InstrumentType[instrument.lower()].value
                except KeyError:
                    # if an unknown type is recieved consider this an 'other' event
                    inst_type = models.InstrumentType['other'].value

                instr = models.Instrument(event=event, name=instrument, instrument_type=inst_type)
                instr.save()
                time_inst = timer()
                print(f'Instrument: {(time_inst-time_event)}')
            else:
                event = models.Event.objects.get(mission=mission, event_id=event)
                time_event = timer()
                print(f'Event: {(time_event-time_var)}')

            evt_type_t = buffer.pop("Action").lower().replace(' ', '_')

            # this is a 'naive' date time with no time zone. But it should always be in UTC
            time = f"{time_position[1][0:2]}:{time_position[1][2:4]}:{time_position[1][4:6]}"
            date_time = datetime.strptime(f"{time_position[0]} {time} +00:00", '%Y-%m-%d %H:%M:%S %z')

            lat = convertDMS_degs(time_position[2])
            lon = convertDMS_degs(time_position[3])

            comment = buffer.pop("Comment")

            time_date_lat = timer()
            print(f'date time: {(time_date_lat-time_event)}')
            try:
                evt_type = models.ActionType[evt_type_t].value
            except KeyError:
                # if an unknown type is received consider this an 'other' event
                evt_type = models.ActionType['other'].value

            action = models.Action(file=log_file, event=event,
                                   date_time=date_time, latitude=lat, longitude=lon,
                                   mid=mid_obj, action_type=evt_type, comment=comment)
            action.save()

            time_action = timer()
            print(f'actions: {(time_action-time_date_lat)}')
            fields = []
            for key in buffer.keys():
                val = buffer[key]
                f_name = models.get_variable_name(name=key)
                field = models.VariableField(action=action, name=f_name, value=val)
                fields.append(field)

            models.VariableField.objects.bulk_create(fields)
            time_varsfield = timer()
            print(f'varfields: {(time_varsfield-time_action)}')
    except Exception as e:
        error = models.LogError(file=log_file, line=mid_obj, message=f"ERR: {log_file.file.name} processing $@MID@$: "
                                                                     f"{mid_obj}",
                                stack_trace=str(e))
        error.save()


def process_ctd(request):
    ctd_files = []
    updated = []
    errors = []
    if 'fid' in request.GET:
        fid = request.GET["fid"]
        while len(processing) > 2:
            time.sleep(1)

        processing.append(fid)
        ctd_file = models.DataFile.objects.get(pk=fid, file_type=models.FileType.btl.value)

        try:

            read_ctd(ctd_file)
            ctd_files.append(ctd_file)

            post_ctd_validation(ctd_files)
            ctd_file.processed = True
            ctd_file.save()

            updated.append(fid)
        except models.Event.DoesNotExist as e:
            err = models.LogError(file=ctd_file, line=-1, message=f"Error Processing file", stack_trace=str(e))
            err.save()
            errors.append(err)
        finally:
            processing.pop()

    elif 'did' in request.GET:
        did = request.GET["did"]

        post_ctd_validation(ctd_files)

    return JsonResponse({'updated': updated, "errors": [{"pk": e.pk, "line": e.line, "msg": e.message, "trace": e.stack_trace}
                                            for e in errors]})


def read_ctd(ctd_file):
    if models.FileType(ctd_file.file_type) == models.FileType.btl:
        read_btl(ctd_file)


def read_btl(btl_file):
    data_frame = ctd.from_btl(btl_file.file_path)
    metadata = getattr(data_frame, "_metadata")
    header = metadata['header'].split('\n')
    # lat_str = None
    # lon_str = None
    event_number = None

    for h in header:
        if 'event_number:' in h.lower():
            h_str = h.split(":")
            event_number = h_str[1].strip()
        # elif 'cruise:' in h.lower():
        #     h_str = h.split(":")
        #     cruise = h_str[1].strip()
        # elif 'nmea latitude =' in h.lower():
        #     h_str = h.split("=")
        #     lat_str = h_str[1].strip()
        # elif 'nmea longitude =' in h.lower():
        #     h_str = h.split("=")
        #     lon_str = h_str[1].strip()

    # tmp_lat = lat_str.split(" ")
    # lat = round((float(tmp_lat[0]) + float(tmp_lat[1]) / 60) * (-1 if tmp_lat[2] == 'S' else 1), 4)
    #
    # tmp_lon = lon_str.split(" ")
    # long = round((float(tmp_lon[0]) + float(tmp_lon[1]) / 60) * (-1 if tmp_lon[2] == 'W' else 1), 4)

    event = models.Event.objects.get(mission=btl_file.directory.mission,
                                     instrument__instrument_type=models.InstrumentType.ctd.value,
                                     event_id=int(event_number))

    col_headers = []
    for c in data_frame.columns:
        col_headers.append(c)

    pop = ['Bottle', 'Date', 'Statistic']
    for h in pop:
        b_idx = col_headers.index(h)
        col_headers.pop(b_idx)

    columns = []
    for h in col_headers:
        c_name = h
        if len(models.DataColumn.objects.filter(name=c_name)) <= 0:
            columns.append(models.DataColumn(name=c_name))

    if len(columns) > 0:
        models.DataColumn.objects.bulk_create(columns)

    b_mod = []
    for i in range(0, (data_frame.shape[0]), 2):
        bottle_id = data_frame["Bottle"].iloc[i]
        date = data_frame["Date"].iloc[i]

        # assume UTC time if a timezone isn't set
        if not hasattr(date, 'timezone'):
            date = pytz.timezone("UTC").localize(date)

        # remove old bottle data that's being replaced in this event
        models.Bottle.objects.filter(event=event, bottle_number=bottle_id).delete()
        b_mod.append(models.Bottle(event=event, bottle_number=bottle_id, date_time=date))

    models.Bottle.objects.bulk_create(b_mod)

    for c in col_headers:
        data_column = []
        column = models.get_data_column_name(c)
        for i in range(0, data_frame.shape[0], 2):
            bottle_id = data_frame["Bottle"].iloc[i]
            d = data_frame[c].iloc[i]
            bottle = models.Bottle.objects.get(event=event, bottle_number=bottle_id)
            data_column.append(models.BottleData(bottle=bottle, column=column, value=d))

        models.BottleData.objects.bulk_create(data_column)


def post_ctd_validation(ctd_files):
    pass


def load_samples(request, pk):
    errors = []
    type = request.GET['type']
    files = request.FILES

    mission = models.Mission.objects.get(pk=pk)

    file_names = files.keys()
    for fname in file_names:
        f = files[fname]

    for fname in file_names:
        process = models.Processing.objects.get(mission=mission, file_or_operation=fname)
        if type == 'salt':
            errors += load_salt(process, files[fname])
        elif type == 'oxy':
            errors += load_oxy(process, files[fname])
        elif type == 'chl':
            errors += load_chl(process, files[fname])

        # We're done with the process at this point
        process.delete()

    return JsonResponse({"errors": [{"pk": e.pk, "line": e.line, "msg": e.message, "trace": e.stack_trace}
                                            for e in errors]})


def load_oxy(mission_id, stream):
    error = []

    xls_obj = load_workbook(stream, data_only=True)

    sheet = xls_obj.active

    row_count = 0
    for row in sheet.iter_rows(max_col=15, values_only=True):
        try:
            row_count += 1
            sample = row[0]
            bottle = row[1]
            o2 = row[2]
            volume = row[10]
            notes = row[13]

            if sample is None and bottle is None and o2 is None and volume is None:
                break  # no more data, break out of the loop rather than read a few hundred blank lines.

            if sample is not None:
                if bottle is None and o2 is None and volume is None:
                    continue
                elif not isfloat(o2):
                    continue

                sample_id = sample.split("_")
                bottle = models.Bottle.objects.get(bottle_number=sample_id[0],
                                                   event__mission_id=mission_id,
                                                   event__instrument__instrument_type=models.InstrumentType.ctd.value)
                if not ocean_models.OxygenSample.objects.filter(bottle_id=bottle.pk).exists():
                    oxy = ocean_models.OxygenSample(bottle=bottle, winklers_1=o2)
                    oxy.bottle.collect_oxygen = True
                    oxy.save()
                else:
                    oxy = ocean_models.OxygenSample.objects.get(bottle_id=bottle.pk)
                    oxy.bottle.collect_oxygen = True
                    oxy.winklers_2 = o2
                    oxy.save()

        except (KeyError, ocean_models.Bottle.DoesNotExist) as e:
            # if the current_id isn't in the samples array a KeyError is thrown, same thing as if we called
            # models.Sample.objects.get(sample_id=current_id) and a DoesNotExist error was thrown.
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=validation.ERR_MISSING_KEY,
                               user_message=f"The requested sample {sample} does not exist")
            err.save()
            error.append(err)
        except validation.ProcessError as e:
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=e.args[0]["error_code"],
                               user_message=e.args[0]["user_message"])
            err.save()
            error.append(err)
        except Exception as e:
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=validation.ERR_UNKNOWN,
                               user_message="An unexpected error has occurred")
            err.save()
            error.append(err)

    return error


def load_salt(process, stream):
    error = []

    xls_obj = load_workbook(stream, data_only=True)

    sheet = xls_obj.active

    # read rows until the first integer
    # row =
    # Prep the ProgressThread table and store the entry
    process.status = 2
    process.end = sheet.max_row
    process.save()

    t = time.time()
    row_count = 0
    scans = []

    for row in sheet.iter_rows(max_col=13, values_only=True):
        try:
            row_count += 1
            sample_id = row[0]
            reading = row[1]
            value = row[2]
            bottle_label = row[3]
            date_time = row[4]
            bath_temp = row[5]
            uncorrected_ratio = row[6]
            uncorrected_ratio_std = row[7]
            correction = row[8]
            adjusted_ratio = row[9]
            calculated_salinity = row[10]
            calculated_salinity_std = row[11]
            comments = row[12]

            if row_count % 50 == 0:
                # DB updates are expensive, by doing a modulus and only updating the progress
                # table every x rows we save a lot of time
                process.current = row_count
                process.save()

            if bottle_label and calculated_salinity and isfloat(calculated_salinity):
                bottle = ocean_models.Bottle.objects.get(bottle_uid=bottle_label,
                                                         activity__sample__set__cruise_id=process.mission.pk,
                                                         activity__instrument__instrument_type=1)  # instrument_type=1 is CTD

                sample = ocean_models.SaltSample(bottle=bottle, sample_id=sample_id,
                                                 calculated_salinity=calculated_salinity,
                                                 comment=comments)
                sample.save()

                sample.created_at = date_time
                sample.bottle.collect_salinity = True
                sample.save()

        except (KeyError, ocean_models.Bottle.DoesNotExist) as e:
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=validation.ERR_MISSING_KEY,
                               user_message=f"The requested sample {bottle_label} does not exist")
            err.save()
            error.append(err)
        except validation.ProcessError as e:
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=e.args[0]["error_code"],
                               user_message=e.args[0]["user_message"])
            err.save()
            error.append(err)
        except Exception as e:
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=validation.ERR_UNKNOWN,
                               user_message="An unexpected error has occurred")
            err.save()
            error.append(err)

    return error


def load_chl(process, stream):
    error = []

    xls_obj = load_workbook(stream, data_only=True)

    sheet = xls_obj.active

    process.end = sheet.max_row
    process.status = 2
    process.save()

    t = time.time()
    row_count = 0
    cur_sample = None
    for row in sheet.iter_rows(max_col=14, values_only=True):
        try:
            row_count += 1
            sample = row[0]
            volume = row[1]
            chl = row[8]
            phae = row[9]
            mean_c = row[12]
            mean_p = row[13]

            if row_count % 50 == 0:
                # DB updates are expensive, by doing a modulus and only updating the progress
                # table every x rows we save a lot of time
                process.current = row_count
                process.save()

            if (sample or cur_sample) and chl and phae and isfloat(chl) and isfloat(phae):

                if sample:
                    cur_sample = sample

                bottle = ocean_models.Bottle.objects.get(bottle_uid=cur_sample,
                                                         activity__sample__set__cruise_id=process.mission.pk,
                                                         activity__instrument__instrument_type=1)

                if not ocean_models.ChlSample.objects.filter(bottle=bottle).exists():
                    chl_sample = ocean_models.ChlSample(bottle=bottle)
                    chl_sample.bottle.collect_nutrients = True
                    chl_sample.save()
                else:
                    chl_sample = ocean_models.ChlSample.objects.get(bottle=bottle)

                chl_sub = ocean_models.ChlSubsample(chl_sample=chl_sample, chl=chl, phae=phae)
                chl_sub.save()

        except (KeyError, ocean_models.Bottle.DoesNotExist) as e:
            # if the current_id isn't in the samples array a KeyError is thrown, same thing as if we called
            # models.Sample.objects.get(sample_id=current_id) and a DoesNotExist error was thrown.
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=validation.ERR_MISSING_KEY,
                               user_message=f"The requested sample {sample} does not exist")
            err.save()
            error.append(err)
        except validation.ProcessError as e:
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=e.args[0]["error_code"],
                               user_message=e.args[0]["user_message"])
            err.save()
            error.append(err)
        except Exception as e:
            err = models.Error(mission=process.mission, file_or_operation=process.file_or_operation,
                               line=row_count, stack_trace=traceback.format_exc(),
                               error_code=validation.ERR_UNKNOWN,
                               user_message="An unexpected error has occurred")
            err.save()
            error.append(err)

    return error
