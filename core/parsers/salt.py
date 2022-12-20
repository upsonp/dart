from . import parser_utils
import numbers

from core import models


# Salts have lots of data, we only care about rows where a Bottle Label is present and is an int.
# we need Bottle Label, DateTime, Calculated Salinity and Comments
def parse_dataframe(dataframe) -> [models.SaltSample]:
    label_sample_id = "Sample ID"
    label_bottle_id = "Bottle Label"
    label_datetime = "DateTime"
    label_calculated_salinity = "Calculated Salinity"
    label_comments = "Comments"

    df = dataframe[[label_bottle_id, label_sample_id, label_datetime, label_calculated_salinity, label_comments]]
    # remove columns that do not have a value in the label_id column
    df = df.dropna(subset=[label_bottle_id])
    number_of_rows = df.shape[0]
    samples = []
    for index in range(number_of_rows):
        row = df.iloc[index]
        bottle = row[label_bottle_id]
        # we don't want calibration samples so we only want a row if it is of the type integer.
        if isinstance(bottle, numbers.Integral):
            sample_id = row[label_sample_id]
            date_time = row[label_datetime]
            cal_salinity = row[label_calculated_salinity]
            comments = row[label_comments]
            sample = models.SaltSample(bottle_id=bottle, sample_date=date_time, sample_id=sample_id,
                                       calculated_salinity=cal_salinity, comments=comments)
            samples.append(sample)

    return samples


def load_data(mission_id, stream):
    return parser_utils.load_data(mission_id, stream, models.SaltSample, parse_dataframe)
