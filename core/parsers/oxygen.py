import pandas

from core import models
from core import utils


def load_oxy(mission_id, stream):
    error = []
    file_name = str(stream)
    file = None
    if file_name.lower().endswith(".csv"):
        file = pandas.read_csv(stream, skiprows=9).values
    elif file_name.lower().endswith(".dat"):
        file = pandas.read_csv(stream, skiprows=8).values
    else:
        file = pandas.read_excel(stream, skiprows=8).values

    # remove existing oxygen samples and re-load from file.
    models.OxygenSample.objects.filter(file=file_name, bottle__event__mission_id=mission_id).delete()

    row_count = 0
    oxy_bottles = []
    for row in file:
        row_count += 1
        try:
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
                elif not utils.isfloat(o2):
                    continue

                sample_id = sample.split("_")

                try:
                    bottle = models.Bottle.objects.get(
                        bottle_id=sample_id[0],
                        event__sample_id__lte=sample_id[0],
                        event__end_sample_id__gte=sample_id[0],
                        event__mission_id=mission_id,
                        event__instrument__instrument_type=models.InstrumentType.ctd.value
                    )

                    if sample_id[1] == '1':
                        oxy = models.OxygenSample(file=file_name, bottle=bottle, winkler_1=o2)
                        oxy_bottles.append(oxy)
                    else:
                        oxy_bottles[-1].winkler_2 = o2

                except models.Bottle.DoesNotExist as e:
                    # if the current_id isn't in the samples array a KeyError is thrown, same thing as if we called
                    # models.Sample.objects.get(sample_id=current_id) and a DoesNotExist error was thrown.
                    err = models.Error(mission_id=mission_id, file_name=str(stream),
                                       message=f"Bottle with id {sample_id[0]} Does not exist",
                                       stack_trace=str(e), line=row_count,
                                       error_code=models.ErrorType.missing_id)
                    err.save()
                    error.append(err)

        except Exception as e:
            err = models.Error(mission_id=mission_id, file_name=str(stream),
                               message=f"Unexpected error processing file", stack_trace=str(e),
                               line=row_count)
            err.save()
            error.append(err)

    models.OxygenSample.objects.bulk_create(oxy_bottles)
    return error
