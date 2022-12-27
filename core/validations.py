from . import models


def validate_ctd_event(event: models.Event, log_file: models.DataFile) -> list[models.Error]:
    errors = []
    mission = event.mission
    mid = event.actions.all()[0].mid
    event_id = event.event_id
    start_sample_id = event.sample_id
    end_sample_id = event.end_sample_id
    if not start_sample_id:
        err = models.Error(
            mission=mission, file_name=log_file.file.name, line=mid,
            message=f"Event {event_id} in file {log_file.file.name} is missing a starting sample ID",
            error_code=models.ErrorType.missing_id
        )
        errors.append(err)

    if not end_sample_id:
        err = models.Error(
            mission=mission, file=log_file, file_name=log_file.file, line=mid,
            message=f"Event {event_id} in file {log_file.file.name} is missing an end sample ID",
            error_code=models.ErrorType.missing_id
        )
        errors.append(err)

    # ctd event start id must be less than or equal to the end id
    if start_sample_id and end_sample_id and start_sample_id > end_sample_id:
        err = models.Error(
            mission=mission, file=log_file, file_name=log_file.file, line=mid,
            message=f"Event {event_id} in file {log_file.file.name} sample id '{start_sample_id}' is larger than end "
                    f"sample id '{end_sample_id}", error_code=models.ErrorType.bad_id
        )
        errors.append(err)

    return errors


def validate_ringnet_event(event: models.Event, log_file: models.DataFile) -> list[models.Error]:
    errors = []
    
    mission = event.mission
    mid = event.actions.all()[0].mid
    event_id = event.event_id
    start_sample_id = event.sample_id
    end_sample_id = event.end_sample_id
    
    if not event.attachments.all().exists():
        err = models.Error(
            mission=mission, file=log_file, file_name=log_file.file, line=mid,
            message=f"Event {event_id} in file {log_file.file.name} does not specify the type of net used as an "
                    f"attachment",
            error_code=models.ErrorType.missing_information)
        errors.append(err)

    if '202um' in [attachment.name for attachment in event.attachments.all()]:
        if start_sample_id and not models.Event.objects.filter(instrument__instrument_type=models.InstrumentType.ctd,
                                                               sample_id=start_sample_id).exists():
            err = models.Error(
                mission=mission, file=log_file, file_name=log_file.file, line=mid,
                message=f"Event {event_id} in file {log_file.file.name} - 202um ringnets must have a sample id "
                        f"corresponding to a CTD bottom id",
                error_code=models.ErrorType.bad_id
            )
            errors.append(err)

    if '76um' in [attachment.name for attachment in event.attachments.all()]:
        if start_sample_id and not models.Event.objects.filter(instrument__instrument_type=models.InstrumentType.ctd,
                                                             end_sample_id=start_sample_id).exists():
            err = models.Error(
                mission=mission, file=log_file, file_name=log_file.file, line=mid,
                message=f"Event {event_id} in file {log_file.file.name} - 76um ringnets must have a sample id "
                        f"corresponding to a CTD surface id", error_code=models.ErrorType.bad_id
            )

            errors.append(err)

    return errors


def validate_events(log_file):

    errors = []

    events = models.Event.objects.filter(actions__file=log_file).distinct()
    for e in events:
        # no need to process this if one of the actions is an aborted action > 0
        if e.actions.filter(action_type=models.ActionType.aborted.value).exists():
            break

        if e.instrument.instrument_type == models.InstrumentType.ctd:
            errors += validate_ctd_event(event=e, log_file=log_file)
        elif e.instrument.instrument_type == models.InstrumentType.ringnet.value:
            errors += validate_ringnet_event(event=e, log_file=log_file)

    if len(errors) > 0:
        models.Error.objects.bulk_create(errors)

    return errors


def validate_bottle_sample_range(file: str, event: models.Event, bottle_id: int, line: int) -> list[models.Error]:
    mission = event.mission
    errors = []
    if event.instrument.instrument_type == models.InstrumentType.ctd and bottle_id > event.end_sample_id:
        err = models.Error(mission=mission, file_name=file, line=line,
                           message=f"Warning: Bottle ID ({bottle_id}) for event {event.event_id} is outside the "
                                   f"ID range {event.sample_id} - {event.end_sample_id}",
                           stack_trace="",
                           error_code=models.ErrorType.bad_id)
        errors.append(err)

    return errors
