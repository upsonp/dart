from core import models

from . import parser_utils

CHN_REQUIRED_HEADERS = ['I.D.', 'C/L(micrograms/litre)', 'N/L(micrograms/litre)', 'C/N']


# CHN is done in pairs and we need I.D., C/L(micrograms/litre), N/L(micrograms/litre) and C/N columns
def parse_dataframe(file_name, dataframe) -> [models.ChnSample]:
    label_id = CHN_REQUIRED_HEADERS[0]
    label_carbon = CHN_REQUIRED_HEADERS[1]
    label_nitrogen = CHN_REQUIRED_HEADERS[2]
    label_carbon_nitrogen = CHN_REQUIRED_HEADERS[3]
    df = dataframe[[label_id, label_carbon, label_nitrogen, label_carbon_nitrogen]]
    number_of_rows = df.shape[0]
    samples = []
    for index in range(0, number_of_rows, 2):
        row1 = df.iloc[index]
        row2 = df.iloc[index+1]

        sample_1 = models.ChnSample(file=file_name, bottle_id=int(row1[label_id]), sample_order=1,
                                    carbon=row1[label_carbon], nitrogen=row1[label_nitrogen],
                                    carbon_nitrogen=row1[label_carbon_nitrogen])

        sample_2 = models.ChnSample(file=file_name, bottle_id=int(row2[label_id]), sample_order=2,
                                    carbon=row2[label_carbon], nitrogen=row2[label_nitrogen],
                                    carbon_nitrogen=row2[label_carbon_nitrogen])

        samples.append(sample_1)
        samples.append(sample_2)

    return samples


def load_data(mission_id, stream):
    return parser_utils.load_data(mission_id, stream, models.ChnSample, parse_dataframe, CHN_REQUIRED_HEADERS)
