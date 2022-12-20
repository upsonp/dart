import pandas as pd

from core import models


# Figure out what row is the header row and return the data under that
def get_dataframe(stream):
    # read the first 10 rows from the file to locate the header row
    df = pd.read_excel(io=stream, sheet_name=0, nrows=10)

    # pandas does a good job at figuring out how many columns there are, but
    # this will only work if all columns have a header value
    number_of_columns_found = len(df.keys())
    while df.keys()[number_of_columns_found-1] == 'Unnamed: ' + str(number_of_columns_found-1):
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header

    df = pd.read_excel(io=stream, sheet_name=0, skiprows=df.index.start)
    return df


# replace the bottle id found in the dataframe with the bottle object ID, which hopefully already exists
def replace_sample_ids(mission_id, file_name, samples):
    errors = []
    create_samples = []
    for sample in samples:
        bottle_id = sample.bottle_id
        try:
            bottle = models.Bottle.objects.get(event__mission=mission_id, bottle_id=bottle_id,
                                               event__instrument__instrument_type=models.InstrumentType.ctd.value)
            sample.bottle_id = bottle.pk
            create_samples.append(sample)
        except models.Bottle.DoesNotExist as e:
            error = models.Error(mission_id=mission_id, error_code=models.ErrorType.missing_id,
                                 file_name=file_name, stack_trace=str(e), line=bottle_id,
                                 message=f'Bottle with id {bottle_id} does not exist')
            errors.append(error)

    return [errors, create_samples]


def load_data(mission_id, stream, model, parse_dataframe):

    file_name = str(stream)
    # remove existing samples associated with the provided stream and re-load from file.
    model.objects.filter(file=file_name, bottle__event__mission_id=mission_id).delete()

    # 1. get the dataframe from the proper header
    dataframe = get_dataframe(stream)

    # 2. parse the dataframe and create the sample objects
    samples = parse_dataframe(dataframe)

    # 3. locate the bottles and associate them with the samples
    errors, create_samples = replace_sample_ids(mission_id, file_name, samples)

    # 4. create the samples
    model.objects.bulk_create(create_samples)

    # 5. return errors for bottles that don't exist
    return errors
