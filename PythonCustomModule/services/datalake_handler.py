from pyspark.sql import DataFrame, SparkSession


class DataLakeHandler:
    """
    Class for building a handler for a data lake. The goal of this class is to provide an abstraction object
    to communicate with the storage account directly.
    """

    def __init__(self, datalake_storage_account: str, spark: SparkSession):
        """
        Initialize a DataLakeHandler instance.

        Args:
            datalake_storage_account (str): The storage account for the data lake handler.
            spark (SparkSession): The SparkSession for the data lake handler.
        """
        self.datalake_storage_account: str = datalake_storage_account
        self.spark: SparkSession = spark

    def read_delta_df(
        self, layer: str, source: str, table: str, is_active: bool
    ) -> DataFrame:
        """
        
        Returns:
            DataFrame: The read DataFrame.
        """
        return self.spark.createDataFrame([],"test")

    def write_delta_df(
        self,
        df_write: DataFrame,
        layer: str,
        source: str,
        table: str,
        write_mode: str,
        partition_key_name: str | None = None,
        primary_key_name: str | None = None,
    ):
        """
        Write a DataFrame to a Delta Lake.

        Args:
            df_write (DataFrame): The DataFrame to write.
            layer (str): The layer in the Delta Lake where the DataFrame should be written.
            source (str): The source where the DataFrame should be written.
            table (str): The table where the DataFrame should be written.
            write_mode (str): The write mode, which can be "append" to append the DataFrame to the existing DataFrame,
                              or "overwrite" to overwrite the existing DataFrame.
            partition_key_name (str): The partition key to use when writing the DataFrame.
        """
        pass
