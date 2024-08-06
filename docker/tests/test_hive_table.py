from pyspark.sql import SparkSession
import pyhive.hive
import unittest

class TestHiveTableCreation(unittest.TestCase):

    def setUp(self):
        # Initialize Spark session with Hive support
        self.spark = SparkSession.builder \
            .appName("HiveTableTest") \
            .enableHiveSupport() \
            .getOrCreate()

    def tearDown(self):
        # Stop the Spark session
        self.spark.stop()

    def test_create_hive_table(self):
        # Create a Hive table using Spark
        self.spark.sql("CREATE TABLE IF NOT EXISTS test_table (id INT, name STRING)")

        # Stop the Spark session
        self.spark.stop()

        # Connect to Hive
        conn = pyhive.hive.connect('localhost')
        cursor = conn.cursor()

        # Query Hive metastore to check if the table exists
        cursor.execute("SHOW TABLES LIKE 'test_table'")
        result = cursor.fetchall()

        # Assert that the table has been created
        self.assertTrue(len(result) > 0, "Hive table 'test_table' was not created.")

if __name__ == '__main__':
    unittest.main()