from abc import ABC, abstractmethod

from pyspark import StorageLevel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

from .datalake_handler import DataLakeHandler


class DataLakeCatalogItemBase(ABC):
    """
    Abstract base class for items in the Data Lake Catalog.
    """

    def __init__(self, name, datalake_handler: DataLakeHandler):
        """
        Initialize a DataLakeCatalogItemBase instance.

        Args:
            name (str): The name of the catalog item.
            datalake_handler (DataLakeHandler, optional): The handler for the data lake. Defaults to DataLakeHandler.
        """
        self.name: str = name
        self.datalake_handler: DataLakeHandler = datalake_handler
        self._dataframe = None

    @abstractmethod
    def get_dataframe(self):
        """
        Abstract method to get the DataFrame associated with the catalog item.
        """

    @abstractmethod
    def reset_dataframe(self):
        """
        Abstract method to reset the DataFrame associated with the catalog item.
        """

    @abstractmethod
    def update_dataframe(
        self,
        df_append: DataFrame,
        partition_key: str | None = None,
        primary_key: str | None = None,
        mode: str = "append",
    ):
        """
        Update the DataFrame associated with the catalog item in the Delta Lake.

        This method writes a DataFrame to the Delta Lake, appending or overwriting the existing DataFrame
        based on the specified mode. After the update, the DataFrame associated with the catalog item is reset.

        Args:
            df_append (DataFrame): The DataFrame to write to the Delta Lake.
            partition_key (str): The partition key to use when writing the DataFrame.
            mode (str, optional): The write mode, which can be "append" to append the DataFrame to the existing DataFrame,
                                or "overwrite" to overwrite the existing DataFrame. Defaults to "append".
        """


class DataLakeCatalogItemFromDataFrame(DataLakeCatalogItemBase):
    """
    Class for catalog items that are created from a DataFrame.
    """

    def __init__(
        self,
        name,
        df_input: DataFrame,
        datalake_handler: DataLakeHandler,
    ):
        """
        Initialize a DataLakeCatalogItemFromDataFrame instance.

        Args:
            name (str): The name of the catalog item.
            df_input (DataFrame): The input DataFrame.
            datalake_handler (DataLakeHandler, optional): The handler for the data lake. Defaults to DataLakeHandler.
        """
        super().__init__(name, datalake_handler)
        self._dataframe = df_input
        self.name = name

    def reset_dataframe(self):
        """
        Reset the DataFrame associated with the catalog item.
        """

    def get_dataframe(self, override: bool=False) -> DataFrame:
        """
        Returns the DataFrame associated with the catalog item.
        """
        return self._dataframe

    def update_dataframe(
        self,
        df_append: DataFrame,
        partition_key: str | None = None,
        primary_key: str | None = None,
        mode: str = "append",
    ):
        """
        Update the DataFrame associated with the catalog item in the Delta Lake.

        This method writes a DataFrame to the Delta Lake, appending or overwriting the existing DataFrame
        based on the specified mode. After the update, the DataFrame associated with the catalog item is reset.

        Args:
            df_append (DataFrame): The DataFrame to write to the Delta Lake.
            partition_key (str): The partition key to use when writing the DataFrame.
            mode (str, optional): The write mode, which can be "append" to append the DataFrame to the existing DataFrame,
                                or "overwrite" to overwrite the existing DataFrame. Defaults to "append".
        """
        self._dataframe = self._dataframe.unionByName(df_append)

class DataLakeCatalog(dict):
    """
    Class representing a catalog of items in a data lake. This class extends the built-in dict class.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a DataLakeCatalog instance. This method accepts the same arguments as the built-in dict class.
        """
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        """
        Set an item in the catalog. The value must be an instance of DataLakeCatalogItemBase.

        Args:
            key (str): The key for the item.
            value (DataLakeCatalogItemBase): The value for the item.

        Raises:
            ValueError: If the value is not an instance of DataLakeCatalogItemBase.
        """
        if not isinstance(value, DataLakeCatalogItemBase):
            raise ValueError("Value must be an instance of DataLakeCatalogItemBase")
        super().__setitem__(key, value)

    def update(self, other: DataLakeCatalogItemBase):
        """
        Update the catalog with another item.

        Args:
            other (DataLakeCatalogItemBase): The item to add to the catalog.
        """
        self.__setitem__(other.name, other)