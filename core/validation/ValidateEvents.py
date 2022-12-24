from core import models
from typing import Callable

# all event validation functions should take an event, test some aspect of the event and then
# return a list of tuples of error_code and message pairs if validation fails, or an empty list
EventValidationFunction = Callable[[models.Event], list[tuple[models.ErrorType, str]]]


def validate_ctd_event(ctd_event: models.Event) -> list[(models.ErrorType, str)]:
    """
    Check that the sample id exists, end sample id exists, and that the sample id is less than the end sample id for
    an event. If the event fails the validation return a list of tuples containing an error code and message
    """
    errors = []
    if ctd_event.sample_id is None:
        errors += [(models.ErrorType.missing_id, f'CTD Event {ctd_event.event_id} is missing a starting sample id')]

    if ctd_event.end_sample_id is None:
        errors += [(models.ErrorType.missing_id, f'CTD Event {ctd_event.event_id} is missing an end sample id')]

    # if we're missing a sample_id or end_sample_id, we can't compare them to see if sample_id < end_sample_id
    if errors:
        return errors
    elif ctd_event.sample_id >= ctd_event.end_sample_id:
        return [(
            models.ErrorType.bad_id,
            f'CTD Event {ctd_event.event_id} sample id {ctd_event.sample_id} must be less than the end sample id ' \
            f'{ctd_event.end_sample_id}'
        )]

    return []


def validate_76_net_event(net_event: models.Event) -> list[(models.ErrorType, str)]:
    """ check that a CTD event exists for this 76 ringnet """
    events = models.Event.objects.filter(instrument__instrument_type=models.InstrumentType.ctd,
                                         end_sample_id=net_event.sample_id)
    if not events.exists():
        return [(
            models.ErrorType.bad_id,
            f"Cannot find matching CTD event for RingNet Event {net_event.event_id} "
            f"with sample id {net_event.sample_id}"
        )]

    return []


def validate_202_net_event(net_event: models.Event) -> list[(models.ErrorType, str)]:
    """ check that a CTD event exists for this 202 ringnet """
    events = models.Event.objects.filter(instrument__instrument_type=models.InstrumentType.ctd,
                                         sample_id=net_event.sample_id)
    if not events.exists():
        return [(
            models.ErrorType.bad_id,
            f"Cannot find matching CTD event for RingNet Event {net_event.event_id} "
            f"with sample id {net_event.sample_id}"
        )]

    return []


def validate_net_event(net_event: models.Event) -> list[(models.ErrorType, str)]:
    """
    Check that the sample id is set and that a corresponding CTD event with a matching bottom or top id exists
    """

    errors = []
    if net_event.sample_id is None:
        errors += [(
            models.ErrorType.missing_id,
            f"Event {net_event.event_id} is missing a Sample ID"
        )]
    attachments = net_event.attachments.all()
    if not attachments.exists():
        return errors + [(models.ErrorType.missing_information,
                          f"Event {net_event.event_id} is missing attachments 76um or 202um")]

    attachments_list = [attachment.name for attachment in attachments]

    if "76um" in attachments_list:
        errors += validate_76_net_event(net_event)

    if "202um" in attachments_list:
        errors += validate_202_net_event(net_event)

    return errors


def validate_event(event: models.Event) -> list[(models.ErrorType, str)]:
    """
    Check that an event has a recognized instrument, which is used to determine what other validation is required
    """
    if event.event_id is None:
        return [(models.ErrorType.missing_id, f"Events are required to have an event id")]

    errors = []
    if event.instrument is None:
        errors += [(models.ErrorType.missing_information, f"No instrument has been assigned to event {event.event_id}")]

    if event.instrument.instrument_type == models.InstrumentType.ctd:
        errors += validate_ctd_event(event)
    elif event.instrument.instrument_type == models.InstrumentType.ringnet:
        errors += validate_net_event(event)
