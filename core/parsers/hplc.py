from . import parser_utils

from core import models


def parse_dataframe(dataframe) -> [models.HplcSample]:
    # I really hate doing things that require long explanations because it probably means I'm doing something wrong :(
    #
    # I got the list of HPLC variables from the DATA_TYPE_METHOD column in HUD2021185_BCD_d table in the existing AZMP
    # Template, which I assume needs to match field names in BioChem. There are a lot of fields, but worse is they don't
    # match the column headers read in from the HPLC xlsx file I'm using for sample data. What I'm going to do here
    # is create a dictionary of the fields in the HPLC model matching the verbose names to the xlsx file and the
    # attribute names to the DATA_TYPE_METHOD names, then I'll use that to iterate over the data and populate the
    # HPLC object to be created. I'm skipping the first three fields in the object because they are the
    # pk (that all Django objects get) and the bottle_id and file field that come from the models.Sample object all
    # sample Objects are extend from.
    labels_attribute_map = {field.verbose_name: field.attname for field in models.HplcSample._meta.fields[3:]}

    labels = ['ID'] + [key for key in labels_attribute_map.keys()]
    df = dataframe[labels]
    number_of_rows = df.shape[0]
    samples = []
    for index in range(number_of_rows):
        row = df.iloc[index]
        bottle_id = int(row[labels[0]])
        sample = models.HplcSample(bottle_id=bottle_id)
        for label_index in range(1, len(labels)):
            label = labels[label_index]
            setattr(sample, labels_attribute_map[label], row[label])

        samples.append(sample)

    return samples


def load_data(mission_id, stream):
    return parser_utils.load_data(mission_id, stream, models.HplcSample, parse_dataframe)