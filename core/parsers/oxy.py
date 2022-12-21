from . import parser_utils

from core import models


# Oxygen is done in pairs and we need Sample and O2_Concentration(ml/l) columns
def parse_dataframe(file_name, dataframe) -> [models.ChnSample]:
    label_id = 'Sample'
    label_winkler = 'O2_Concentration(ml/l)'
    df = dataframe[[label_id, label_winkler]]
    number_of_rows = df.shape[0]
    samples = []
    cur_sample = None
    for index in range(number_of_rows):
        row = df.iloc[index]
        sample_label = row[label_id].split("_")
        if int(sample_label[1]) == 1:
            cur_sample = models.OxygenSample(file=file_name, bottle_id=int(sample_label[0]),
                                             winkler_1=row[label_winkler])
            samples.append(cur_sample)
        else:
            cur_sample.winkler_2 = row[label_winkler]

    return samples


def load_data(mission_id, stream):
    return parser_utils.load_data(mission_id, stream, models.OxygenSample, parse_dataframe)

