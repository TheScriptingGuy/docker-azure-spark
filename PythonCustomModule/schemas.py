from pyspark.sql.types import StructType, StructField, IntegerType


def get_schema(table_name: str) -> StructType:
    """
    This function creates a dictionary of schemas and returns one of them.

    :param table_name: the table for which to get the schema.
    :returns: the schema of the table.
    """

    schema_dict = {
        "value_table": value_table_schema,
    }

    return schema_dict[table_name]

value_table_schema = StructType([
        StructField("value1", IntegerType(), True),
        StructField("value2", IntegerType(), True)
    ])
