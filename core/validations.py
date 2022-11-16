from . import models


def validate_events(log_file):

    errors = []

    events = models.Event.objects.filter(actions__file=log_file).distinct()
    for e in events:
        # no need to process this if one of the actions is an aborted action
        if len(e.actions.filter(action_type=models.ActionType.aborted.value)) > 0:
            break

        if e.instrument.instrument_type == models.InstrumentType.ctd.value:
            # ctd events must have a start and end id

            if not e.sample_id:

                err = models.Error(mission=e.mission, file=log_file, file_name=log_file.file,
                                   line=e.actions.all()[0].mid,
                                   message=f"Event {e.event_id} in file {log_file.file.name}"
                                           f" is missing a starting sample ID",
                                   error_code=models.ErrorType.missing_id)
                errors.append(err)

            if not e.end_sample_id:
                err = models.Error(mission=e.mission, file=log_file, file_name=log_file.file,
                                   line=e.actions.all()[0].mid,
                                   message=f"Event {e.event_id} in file {log_file.file.name}"
                                           f" is missing an end sample ID",
                                   error_code=models.ErrorType.missing_id)
                errors.append(err)

            # ctd event start id must be less than or equal to the end id
            if e.sample_id and e.end_sample_id and e.sample_id > e.end_sample_id:
                err = models.Error(mission=e.mission, file=log_file, file_name=log_file.file,
                                   line=e.actions.all()[0].mid,
                                   message=f"Event {e.event_id} in file {log_file.file.name}"
                                           f" sample id '{e.sample_id}' is larger than end"
                                           f" sample id '{e.end_sample_id}",
                                   error_code=models.ErrorType.bad_id.value)
                errors.append(err)

        elif e.instrument.instrument_type == models.InstrumentType.ringnet.value:

            if len(e.instrument.attachments.all()) <= 0:
                err = models.Error(mission=e.mission, file=log_file, file_name=log_file.file,
                                   line=e.actions.all()[0].mid,
                                   message=f"Event {e.event_id} in file {log_file.file.name} does not specify"
                                           f" the type of net used as an attachment",
                                   error_code=models.ErrorType.missing_information)
                errors.append(err)

            if '202um' in [a.name for a in e.instrument.attachments.all()]:
                if e.sample_id and len(models.Event.objects.filter(
                        instrument__instrument_type=models.InstrumentType.ctd.value, sample_id=e.sample_id)) <= 0:
                    err = models.Error(mission=e.mission, file=log_file, file_name=log_file.file,
                                       line=e.actions.all()[0].mid,
                                       message=f"Event {e.event_id} in file {log_file.file.name} - 202um "
                                               f"ringnets must have a sample id corresponding to a CTD "
                                               f"bottom id",
                                       error_code=models.ErrorType.bad_id)
                    errors.append(err)

            if '76um' in [a.name for a in e.instrument.attachments.all()]:
                if e.sample_id and len(models.Event.objects.filter(
                        instrument__instrument_type=models.InstrumentType.ctd.value, end_sample_id=e.sample_id)) <= 0:
                    err = models.Error(mission=e.mission, file=log_file, file_name=log_file.file,
                                       line=e.actions.all()[0].mid,
                                       message=f"Event {e.event_id} in file {log_file.file.name} - 76um "
                                               f"ringnets must have a sample id corresponding to a CTD "
                                               f"surface id",
                                       error_code=models.ErrorType.bad_id)

                    errors.append(err)

    if len(errors) > 0:
        models.Error.objects.bulk_create(errors)

    return errors
