from . import parser_utils

from core import models
import numpy as np


# CHL is done in pairs and we need I.D., CHL. and PHAE. columns
def parse_dataframe(file_name, dataframe) -> [models.ChlSample]:
    label_id = 'I.D.'
    label_chl = 'CHL.'
    label_phae = 'PHAE.'
    df = dataframe[[label_id, label_chl, label_phae]]
    number_of_rows = df.shape[0]
    samples = []
    chl_iterator = iter(range(number_of_rows))
    for index in chl_iterator:
        row1 = df.iloc[index]
        row2 = df.iloc[index+1]

        sample_1 = models.ChlSample(file=file_name, bottle_id=int(row1[label_id]), sample_order=1,
                                    phae=row1[label_phae], chl=row1[label_chl])
        samples.append(sample_1)

        # if row2 has an id then the last sample didn't have a second for some reason.
        # Do not advance the iterator. Row 2 on this iteration will be row 1 on the next iteration
        if not np.isnan(row2[label_id]):
            continue

        sample_2 = models.ChlSample(file=file_name, bottle_id=int(row1[label_id]), sample_order=2,
                                    phae=row2[label_phae], chl=row2[label_chl])
        samples.append(sample_2)
        # Advance the iterator this is the equivalent of stepping through the iterator by 2
        next(chl_iterator, None)

    return samples


def load_data(mission_id, stream):
    return parser_utils.load_data(mission_id, stream, models.ChlSample, parse_dataframe)
