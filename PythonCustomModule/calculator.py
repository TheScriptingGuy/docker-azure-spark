from pyspark.sql import DataFrame

def add_columns(df: DataFrame, col1: str, col2: str):
    return df.withColumn("sum", df[col1] + df[col2])

