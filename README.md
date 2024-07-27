# docker-azure-spark
Development container for Spark with Azure Storage Account (Gen2) Support

# Introduction

## What cases make this docker image useful

This docker image / development container is useful when:
- Using Azure Big Data / Large Scale Analytical Processing engines such as Synapse Analytics, Fabric or Databricks. All of which use Apache Spark.
- Using Azure Storage Account Gen2 to read/write data
- When working with Delta Lake / Lakehouse architectures
- Using Visual Studio Code to develop Spark Applications
- When working with Python in Spark
- When wanting to locally develop in Spark with Python and Jupyter
- When you have a project which has more Python files, modules or projects.
- When working with Docker

This docker image / development container is less useful when:
- Building a Python Spark project fully in notebooks (run magics and notebook utils)
- Working with Spark on other Cloud platforms such as AWS or Google Cloud
- When working with Scala or Dotnet Spark Applications
- When testing workloads in Master / Multi Executor mode
- When you don't have Docker available

## What are the software and attributes of the docker image

Configurable Software Versions of:
- Spark (default 3.3.4)
- Hadoop (default 3.3.4)
- Delta Lake (default 2.2.0)
- Python (default 3.10)

Other software:
Azure Storage Jars
Azure Blob Storage Jars
Node JS

## What is currently supported in this docker image

- Azure Blob (wasbs)
  - Only Reading from Azure Blob Storage (Gen1) is supported for now.
- Azure Storage Account Gen2 (abfss)
  - Reading,writing,deleting, updating are supported. Spark functions well with this kind of storage account
- Spark
  - All normal Spark operations are supported
  - Maven functions
- Running Hadoop
  - All normal Hadoop operations are supported
- Running Apache Livy
  - The Apache Livy REST API is running in the docker container. You can use Livy to control Spark operations using REST calls.
- Running Hive
  - Hive is up and running with a Derby Embedded Database serving as metastore
  - Spark is integrated with hive as the catalog implementation
  - All hive tables are stored in the default directory /user/hive/warehouse
- Jupyter Notebooks
  - Jupyter notebooks are up and running when running the bootstrap.sh
  - Accessible with the default ports: http://localhost:8888
  - Sparkmagic has been installed to optimize Jupyter to work with Spark, Pyspark, Scala and can pretty print tables. Please refer to their github page for documentation.

## How can you use this project

For now it's recommended to only use this project as a development container in vscode. Spark has not been configured to be exposed outside of the container in this first version.

### Preparation steps

Ensure the following extensions are installed in vscode:
- Dev Containers
- Docker

Ensure the following software is installed on your pc:
- Docker
- Alternative: Rancher Desktop
  - Download Rancher Desktop
  - Choose dockerd (moby) as Container Engine
  - Install WSL if prompted
  - Don't use kubernetes (not required)
  - Reboot your computer when installed

Copy the ENVTEMPLATE file and create a new .env file. Configure your Azure storage account in the JSON array and ensure to escape " to ensure it can be processed successfully. If have your own Azure Storage Account, ensure that you have a Private Connection or make sure the storage account can be accessed from your ip on the internet. Also get the storage account key from the Azure Portal by going to the Storage Account and going to the Access Keys tab.

Optional:
Check if the docker compose file works as expected

### Docker Hub

For every Fabric Runtime release, I have created a docker image which can be pulled from docker hub. You can find the project here https://hub.docker.com/repository/docker/portablespark/docker-azure-spark/general

### Run the Dev Container

1. Open the project in vscode
2. Open the Command Palette
3. Search for the command Dev Containers: Rebuild and Reopen in Container
4. The Dev container will start the docker compose process, this will take some time for building the docker container.
5. Check if the dev container starts succesfully

Note: This dev container runs the docker compose file stored in docker/run. It is based on one of the many tags from the project on docker hub. It will use a pre-build image which you can use easily for your projects
   
### Use the example from notebooks/NotebookStorageAccountTest.ipynb

Adjust the code so it runs for your storage accounts to write to Gen2 or to read from Blob. Start the notebook or copy the code in a pyspark cmd.

### Extending the docker image

You can extend the docker image, by extending the python requirement.txt file in the docker directory. The Docker build will install these packages automatically

### Good luck

If it works, good luck with this container. If encountering issues, please reach out.