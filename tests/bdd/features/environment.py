from pyspark.sql import SparkSession

from PythonCustomModule.services.datalake_catalog import DataLakeCatalog
from PythonCustomModule.services.datalake_handler import DataLakeHandler


def before_feature(context, feature):
    # move this to a prepare step
    context.spark = SparkSession.builder.getOrCreate()
    context.catalog = DataLakeCatalog()
    context.datalake_handler = DataLakeHandler("", context.spark)
    pass


def before_scenario(context, scenario):
    pass