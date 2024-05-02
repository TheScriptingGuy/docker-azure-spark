# features/steps/steps.py

from typing import Iterable

from behave import given, then, when  # pylint: disable=no-name-in-module
from behave.model import Table
from behave.runner import Context
from pyspark.sql import DataFrame, SparkSession
from utils.table_builder import TestTableBuilder
from utils.table_to_dataframe_utils import (extract_table_from_context,
                                            table_to_spark)

from PythonCustomModule.calculator import add_columns
from PythonCustomModule.schemas import get_schema


@given("a table {table_name} with the following records")
def step_a_table_x_with_the_following_records(context: Context, table_name: str):

    print(table_name)
    if isinstance(context.table, Table):
        table_data = context.table
    else:
        raise ValueError("No table data is provided.")
    
    schema = get_schema(table_name)

    catalog_item = (
        TestTableBuilder()
        .set_table_name(table_name)
        .set_table_data(table_data)
        .set_datalake_handler(context.datalake_handler)
        .set_schema(schema)
        .build(context.spark)
    )

    context.catalog.update(catalog_item)

    context.catalog[table_name].update_dataframe(catalog_item.get_dataframe())

@when('I add value 1 and value 2')
def step_i_add_value_1_and_value_2(context):
    context.actual_output_df = add_columns(context.catalog["value_table"].get_dataframe(), "value1", "value2")

@then('a new column "sum" is created with the correct values')
def step_check_result(context):
    expected_output_df: DataFrame = table_to_spark(context.spark, context.table)

    # Get the column names from expected_output_df
    column_names = expected_output_df.columns

    # Select the columns from output_possiblematches_df
    output_df = context.actual_output_df.select(*column_names)

    # Check if the two DataFrames are equal
    assert output_df.subtract(expected_output_df).count() == 0 and expected_output_df.subtract(output_df).count() == 0, "DataFrames are not equal"

