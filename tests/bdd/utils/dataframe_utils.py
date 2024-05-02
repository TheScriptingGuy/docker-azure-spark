from pyspark.sql import SparkSession
from pyspark.sql import types as T
from PythonCustomModule.services.datalake_catalog import DataLakeCatalogItemFromDataFrame
from PythonCustomModule.services.datalake_handler import DataLakeHandler

def create_empty_dataframe(spark: SparkSession, datalake_handler: DataLakeHandler, table_name: str, schema: T.StructType):
    """
    Create an empty dataframe according the provided schema.

    Args:
        spark (SparkSession): The SparkSession to use for creating the DataFrame.
        datalake_handler (DataLakeHandler): The datalake handler
        schema (StructType): The schema of the table

    Returns:
        DataLakeCatalogItemFromDataFrame: A Spark DataFrame in a DataLakeCatalogItem object.
    """
    dataframe = spark.createDataFrame([], schema)

    return DataLakeCatalogItemFromDataFrame(
        table_name,
        dataframe,
        datalake_handler=datalake_handler,
    )
