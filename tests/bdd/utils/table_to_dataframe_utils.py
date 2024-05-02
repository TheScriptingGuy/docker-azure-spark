import ast
import json
import random
import re
import string
import time
from datetime import datetime

from behave.model import Table
from behave.runner import Context
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import types as T
from pyspark.sql.functions import array, expr, lit, slice, to_timestamp, udf

# Mapping of Python datetime formats to PySpark formats
datetime_formats = {
    "%d-%b-%Y": "dd-MMM-yyyy",
    "%Y-%m-%d %H:%M:%S": "yyyy-MM-dd HH:mm:ss",
    "%Y-%m-%d": "yyyy-MM-dd",
    "%m/%d/%Y": "MM/dd/yyyy",
    "%m/%d/%Y %H:%M:%S": "MM/dd/yyyy HH:mm:ss",
}


def string_to_type(s: str):
    """
    Infer the pyspark type of a string
    Args:
        s (str): The value.
    Returns:
        pyspark.sql.types: The type.
    """
    tname = s.lower()
    if tname == "int":
        return T.IntegerType()
    elif tname in ["long", "timestamp"]:
        return T.LongType()
    elif tname == "double":
        return T.DoubleType()
    else:
        return T.StringType()


def random_cell(mode: str):
    """
    Generate random string to use in a cell.
    TODO: do we need to support ftype?
    Args:
        mode (str): The value of the mode in the following structure: "^.*RAND(\\((\\d+)-(\\d+)\\))?.*$"
    Returns:
        str: Random string.
    """
    r = re.compile(r"^.*RAND(\((\d+)-(\d+)\))?.*$")
    matches = r.match(mode)
    if matches is None:
        lower, upper = 0, 2147483647
    else:
        (_, l, u) = matches.groups()
        lower = int(l) if l else 0
        upper = int(u) if u else 2147483647
    string_length = random.randint(lower, upper)
    return "".join(random.choices(string.ascii_lowercase, k=string_length))


def seq_cell(sequence_positions, inflect_engine, name, field_type):
    val = sequence_positions.get(name, 0) + 1
    sequence_positions[name] = val

    dt = field_type.lower()
    if dt in ["int", "long", "timestamp"]:
        return val
    if dt == "double":
        return float(val)
    elif dt in ["string", "str"]:
        return inflect_engine.number_to_words(val)
    else:
        raise ValueError(f"Data type not supported for sequences {dt}")


def parse_ts(s):
    t = time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))
    return int(t)


def process_cells(cols, cells, schema):
    ## TODO REMOVE
    data = list(zip(cols, cells, schema))
    for _, cell, _ in data:
        if "%RAND" in cell:
            yield random_cell(cell)
        else:
            yield cell


# Function to infer data type
def infer_type(value):
    """
    Infers the datatype from the provided value.

    Args:
        value (Unknown): The value that needs the be inferred.
    Returns:
        pyspark.sql.types: The type of the value.
    Raises:
        ValueError: If the value is not a pyspark sql type of those that we check.
    """
    try:
        for py_format, _ in datetime_formats.items():
            try:
                # Try to parse as datetime
                datetime.strptime(value, py_format)
                # If successful, return the corresponding PySpark format
                return T.TimestampType()
            except ValueError:
                pass
    except ValueError:
        pass

    try:
        # Try to parse as list
        values = ast.literal_eval(value)
        if isinstance(values, list) and all(isinstance(value, int) for value in values):
            return T.ArrayType(T.LongType())
    except (ValueError, SyntaxError):
        pass

    try:
        # Try to parse as integer
        int(value)
        return T.IntegerType()
    except ValueError:
        pass

    try:
        # Try to parse as float
        float(value)
        return T.FloatType()
    except ValueError:
        pass

    try:
        # Try to parse as boolean
        if value.lower() in ["true", "false"]:
            return T.BooleanType()
    except ValueError:
        pass

    # Default to string type
    return T.StringType()


def infer_datatype_from_first_cell(cols: list[str], cells: list):
    """
    Infers the datatype from the first cell in a dataframe.

    Args:
        cols (DataFrame): The DataFrame to be modified.
        schema (StructType): The schema of the DataFrame.

    Returns:
        DataFrame: The DataFrame with converted column types.
    """
    data = list(zip(cols, cells))
    schema = []
    for col, cell in data:
        schema.append(T.StructField(name=col, dataType=infer_type(cell)))
    return T.StructType(fields=schema)


def convert_column_types(df, schema) -> DataFrame:
    """
    Convert string columns in DataFrame to appropriate data types based on the provided schema.

    Args:
        df (DataFrame): The DataFrame to be modified.
        schema (StructType): The schema of the DataFrame.

    Returns:
        DataFrame: The DataFrame with converted column types.
    """
    for field in schema:

        first_value = df.select(field.name).first()[0]
        if isinstance(field.dataType, T.TimestampType):
            df = convert_to_timestamp(df, field, first_value)
        if isinstance(field.dataType, T.ArrayType) and isinstance(
            field.dataType.elementType, T.LongType
        ):
            df = convert_to_array_long(df, field, first_value)
        elif isinstance(field.dataType, T.IntegerType):
            df = convert_to_integer(df, field, first_value)
        elif isinstance(field.dataType, T.FloatType):
            df = convert_to_float(df, field, first_value)
        elif isinstance(field.dataType, T.BooleanType):
            df = convert_to_boolean(df, field, first_value)
    return df


def convert_to_array_long(df, field, first_value):
    """
    Convert string column to array(integer) type if possible.

    Args:
        df (DataFrame): The DataFrame to be modified.
        field (StructField): The field information.
        first_value (str): The first value of the column.
    """
    try:

        def parse_array_from_string(x):
            res = json.loads(x)
            return res

        retrieve_array = udf(parse_array_from_string, T.ArrayType(T.LongType()))

        if len(first_value) > 0:
            values = ast.literal_eval(first_value)
            if isinstance(values, list) and all(isinstance(value, int) for value in values):
                return df.withColumn(field.name, retrieve_array(df[field.name]))
        else:
            return df.withColumn(field.name, array().cast(T.ArrayType(T.LongType())))
    except (ValueError, SyntaxError):
        return df


def convert_to_timestamp(df, field, first_value):
    """
    Convert string column to timestamp type if possible.

    Args:
        df (DataFrame): The DataFrame to be modified.
        field (StructField): The field information.
        first_value (str): The first value of the column.
    """
    for py_format, spark_format in datetime_formats.items():
        try:
            datetime.strptime(first_value, py_format)
            return df.withColumn(field.name, to_timestamp(df[field.name], spark_format))
        except ValueError:
            return df


def convert_to_integer(df, field, first_value):
    """
    Convert string column to integer type if possible.

    Args:
        df (DataFrame): The DataFrame to be modified.
        field (StructField): The field information.
        first_value (str): The first value of the column.
    """
    try:
        int(first_value)
        return df.withColumn(field.name, df[field.name].cast(T.IntegerType()))
    except ValueError:
        return df


def convert_to_float(df, field, first_value):
    """
    Convert string column to float type if possible.

    Args:
        df (DataFrame): The DataFrame to be modified.
        field (StructField): The field information.
        first_value (str): The first value of the column.
    """
    try:
        float(first_value)
        return df.withColumn(field.name, df[field.name].cast(T.FloatType()))
    except ValueError:
        return df


def convert_to_boolean(df, field, first_value):
    """
    Convert string column to boolean type if possible.

    Args:
        df (DataFrame): The DataFrame to be modified.
        field (StructField): The field information.
        first_value (str): The first value of the column.
    """
    try:
        if first_value.lower() in ["true", "false"]:
            return df.withColumn(field.name, df[field.name].cast(T.BooleanType()))
    except ValueError:
        return df


def table_to_spark(spark: SparkSession, table) -> DataFrame:
    """
    Convert a table data into a Spark DataFrame.
    The columns and their data types are inferred from the table's headings and
    the first row of data.

    Args:
        spark (SparkSession): The SparkSession to use for creating the DataFrame.
        table (behave table): The tabular data.

    Returns:
        DataFrame: A Spark DataFrame representing the tabular data with inferred schema and column types.

    Raises:
        ValueError: If the table headings or data cells are improperly formatted.
    """
    cols = [h.split(":") for h in table.headings]

    if len([c for c in cols if len(c) != 2]) > 0:
        cols = [h for h in table.headings]

    schema = T.StructType([T.StructField(name, T.StringType(), False) for name in cols])
    new_schema = infer_datatype_from_first_cell(cols, table[0].cells)

    rows = [list(row.cells) for row in table]
    df = spark.createDataFrame(rows, schema=schema)

    # Convert column types
    df = convert_column_types(df, new_schema)

    return df


def extract_table_from_context(behave_context: Context) -> Table:
    """
    Extracts the table from the behave context.
    Args:
        behave_context (Context): The  behave context
    Returns:
        Table: The tabular data in the behave context.
    Raises:
        ValueError: If table is not in the behave context
    """
    if isinstance(behave_context.table, Table):
        return behave_context.table
    else:
        raise ValueError("No table data is provided.")
