from pyspark.sql import SparkSession
import subprocess
import unittest


class TestHiveTableCreation(unittest.TestCase):

    def setUp(self):
        # Initialize Spark session with Hive support
        self.spark = SparkSession.builder.appName("HiveTableTest").enableHiveSupport().getOrCreate()

    def tearDown(self):
        # Stop the Spark session
        self.spark.stop()

    def test_create_hive_table(self):
        # Create a Hive table using Spark
        self.spark.sql("CREATE TABLE IF NOT EXISTS test_table (id INT, name STRING)")

        # Stop the Spark session
        self.spark.stop()

        # Connect to Hive using Beeline and check if the table exists
        beeline_cmd = """
        beeline -u 'jdbc:hive2://localhost:10000/default' -e "SHOW TABLES LIKE 'test_table'"
        """
        result = subprocess.run(beeline_cmd, shell=True, capture_output=True, text=True)

        # Assert that the table has been created
        self.assertIn("test_table", result.stdout, "Hive table 'test_table' was not created.")


if __name__ == "__main__":
    unittest.main()
