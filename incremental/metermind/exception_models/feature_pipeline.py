from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import constants

MODELLING_NUMBER_COLUMNS = (
    "sanctioned_load_kw",
    "cycle_days",
    "previous_reading",
    "current_reading",
    "units_consumed",
    "twelve_month_average_units",
    "same_month_last_year_units",
    "consecutive_estimated_reads",
    "days_since_actual_read",
    "neighbourhood_average_units",
)

MODELLING_CATEGORY_COLUMNS = (
    "consumer_category",
    "read_type",
    "seal_check_result",
    "division",
    "meter_make",
)

MODELLING_COLUMNS = MODELLING_NUMBER_COLUMNS + MODELLING_CATEGORY_COLUMNS

DERIVED_NUMBER_COLUMNS = (
    "consumption_ratio_to_average",
    "load_factor",
    "meter_age_years",
)

WIDENED_MODELLING_COLUMNS = MODELLING_COLUMNS + DERIVED_NUMBER_COLUMNS

EXCEPTION_COLUMN = "exception_class"


def modelling_columns(widened=False):
    if widened:
        return WIDENED_MODELLING_COLUMNS
    return MODELLING_COLUMNS


def _one_hot_encoder():
    try:
        return OneHotEncoder(
            handle_unknown="ignore",
            min_frequency=0.01,
            sparse_output=False,
        )
    except TypeError:
        return OneHotEncoder(
            handle_unknown="ignore",
            min_frequency=0.01,
            sparse=False,
        )


def build_feature_pipeline(widened=False):
    number_columns = list(MODELLING_NUMBER_COLUMNS)
    if widened:
        number_columns = number_columns + list(DERIVED_NUMBER_COLUMNS)

    number_steps = Pipeline(
        steps=[
            ("fill", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    category_steps = Pipeline(
        steps=[
            ("fill", SimpleImputer(strategy="most_frequent")),
            ("widen", _one_hot_encoder()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numbers", number_steps, number_columns),
            ("categories", category_steps, list(MODELLING_CATEGORY_COLUMNS)),
        ]
    )


if __name__ == "__main__":
    import pandas as pd

    book = pd.read_csv(constants.CLEAN_READING_BOOK_PATH).head(2000)
    preparation = build_feature_pipeline()
    prepared = preparation.fit_transform(book[list(MODELLING_COLUMNS)])
    print(f"{len(MODELLING_COLUMNS)} columns in, {prepared.shape[1]} numbers out")
