import pandas as pd
import numpy as np
from config import paths
from logger import get_logger
from Classifier import Classifier, predict_with_model
from preprocessing.pipeline import run_pipeline
from schema.data_schema import load_saved_schema
from utils import read_csv_in_directory, save_dataframe_as_csv, ResourceTracker

logger = get_logger(task_name="predict")


def run_batch_predictions(
    test_dir=paths.TEST_DIR,
    predictor_dir=paths.PREDICTOR_DIR_PATH,
    predictions_file_path=paths.PREDICTIONS_FILE_PATH,
    saved_schema_dir=paths.SAVED_SCHEMA_DIR_PATH,
) -> None:
    """
    Run batch predictions on test data, save the predicted probabilities to a CSV file.

    This function reads test data from the specified directory,
    loads the preprocessing pipeline and pre-trained predictor model,
    transforms the test data using the pipeline,
    makes predictions using the trained predictor model,
    adds ids into the predictions dataframe,
    and saves the predictions as a CSV file.
    """
    with ResourceTracker(logger, monitoring_interval=0.1):
        x_test = read_csv_in_directory(test_dir)
        data_schema = load_saved_schema(saved_schema_dir)
        ids = x_test[data_schema.id]
        x_test.drop(columns=data_schema.id, inplace=True)
        x_test = run_pipeline(x_test, data_schema, training=False)
        model = Classifier.load(predictor_dir)

        logger.info("Making predictions...")
        predictions_arr = predict_with_model(model, x_test)

    if data_schema.model_category == 'multiclass_classification':
        predictions_df = pd.DataFrame(predictions_arr, columns=data_schema.target_classes)
    elif data_schema.model_category == 'binary_classification':
        predictions_df = pd.DataFrame(
            np.hstack((1-predictions_arr, predictions_arr)),
            columns=data_schema.target_classes
        )

    predictions_df[data_schema.id] = ids
    logger.info("Saving predictions...")
    save_dataframe_as_csv(dataframe=predictions_df, file_path=predictions_file_path)
    logger.info("Batch predictions completed successfully")


if __name__ == "__main__":
    run_batch_predictions()
