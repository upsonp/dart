from . import parser_utils

from core import models
import numpy as np


# CHL is done in pairs and we need I.D., CHL. and PHAE. columns
def parse_dataframe(dataframe) -> [models.ChlSample]:
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

        sample_1 = models.ChlSample(bottle_id=int(row1[label_id]), sample_order=1, phae=row1[label_phae],
                                    chl=row1[label_chl])
        samples.append(sample_1)

        # if row2 has an id then the last sample didn't have a second for some reason
        # subtract one from the index and continue without a second sample
        if not np.isnan(row2[label_id]):
            continue

        sample_2 = models.ChlSample(bottle_id=int(row1[label_id]), sample_order=2, phae=row2[label_phae],
                                    chl=row2[label_chl])
        samples.append(sample_2)
        next(chl_iterator, None)

    return samples


def load_data(mission_id, stream):
    return parser_utils.load_data(mission_id, stream, models.ChlSample, parse_dataframe)
