"""
The module provides building blocks to create a table based on a Behave data table.
"""

from behave.model import Table
from pyspark.sql import SparkSession
from pyspark.sql import types as T
from pyspark.sql.functions import lit, to_timestamp
from utils.table_to_dataframe_utils import convert_column_types, table_to_spark

from PythonCustomModule.services.datalake_catalog import (
    DataLakeCatalogItemFromDataFrame, DataLakeHandler)


class TestTableBuilder:
    """
    Class for building a spark table with data.
    """

    def __init__(self):
        """
        Initialize a spark table builder.
        """
        self.table_name = None
        self.schema = T.StructType([])
        self.datalake_handler = None
        self.table_data = []
        self.table = Table([])
        self.timestamp_lit = to_timestamp(lit("2022-10-01"), "yyyy-MM-dd")

    def set_timestamp(self, timestamp: str):
        """
        Set the timestamp for default values like the partition key.
        Args:
            timestamp (str | "yyyy-MM-dd"): The timestamp in string format.
        Returns:
            TestTableBuilder: The builder instance.
        """
        self.timestamp_lit = to_timestamp(lit(timestamp), "yyyy-MM-dd")

    def set_schema(self, schema: T.StructType):
        """
        Set the metadata for the catalog.
        Args:
            schema (StructType): The schema for the table.
        Returns:
            TestTableBuilder: The builder instance.
        """
        self.schema = schema
        return self

    def set_datalake_handler(self, datalake_hander: DataLakeHandler):
        """
        Set the data lake handlers for the datalake catelog item.
        Args:
            spark (SparkSession): The SparkSession to use for the data lake handlers.
        Returns:
            TestTableBuilder: The builder instance.
        """
        self.datalake_handler = datalake_hander

        return self

    def set_table_name(self, table_name: str):
        """
        Set table name.

        Args:
            table_name (str): The table name.
        Returns:
            TestTableBuilder: The builder instance.
        """
        self.table_name = table_name
        return self

    def set_table_data(self, table_data: Table):
        """
        Set table data.
        Args:
            table_data (Table): The table records
        Returns:
            TestTableBuilder: The builder instance.
        """
        self.table_data = [list(row.cells) for row in table_data]
        self.table = table_data
        return self

    def transform_data_according_to_schema(self):
        """
        Transform the data into the provided schema format.
        Returns:
            DataLakeCatalog: The built data lake catalog.
        """
        column_order = []
        table_headers = [header.lower() for header in self.table.headings]
        # Map data table to schema
        for schema_header in self.schema:
            try:
                data_column_index = table_headers.index(schema_header.name.lower())
                column_order.append(data_column_index)
            except ValueError:
                column_order.append(-1)

        # Get the number of columns in the original data
        num_columns = len(self.schema.fields) if self.table_data else 0

        # Create a new list of lists where each row contains only empty strings
        transformed_datatable = [
            ["" for _ in range(num_columns)] for _ in range(len(self.table_data))
        ]

        for idx, schema_header in enumerate(self.schema):
            target_column_idx = column_order[idx]
            if target_column_idx != -1:
                # Copy column values from data into the new data table
                for i, row in enumerate(transformed_datatable):
                    row[idx] = self.table_data[i][target_column_idx]

        if len(column_order) != len(self.schema):
            print(f"Table columns are updated {table_headers} != {self.schema}\n\n")
        self.table_data = transformed_datatable

    def build(self, spark: SparkSession):
        """
        Build the data lake catalog.
        Returns:
            DataLakeCatalog: The built data lake catalog.
        Raises:
            ValueError: If no catalog items have been added.
        """
        if not self.datalake_handler or not self.table_name:
            raise ValueError("Missing required parameters")

        if not self.schema or len(self.schema) == 0:
            dataframe = table_to_spark(spark, self.table)
        else:
            self.transform_data_according_to_schema()
            schema = T.StructType(
                [T.StructField(field.name, T.StringType(), False) for field in self.schema]
            )
            dataframe = spark.createDataFrame(self.table_data, schema)
            if dataframe.count() > 0:
                dataframe = convert_column_types(dataframe, self.schema)
            else:
                dataframe = spark.createDataFrame(self.table_data, self.schema)

        return DataLakeCatalogItemFromDataFrame(
            self.table_name,
            dataframe,
            datalake_handler=self.datalake_handler,
        )
