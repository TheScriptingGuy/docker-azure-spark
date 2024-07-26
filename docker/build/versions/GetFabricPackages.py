import json
import requests


def package_exists_on_pypi(package_name, version):
    """
    Check if a specific version of a package exists on PyPI.
    """
    url = f"https://pypi.org/project/{package_name}/{version}/"
    response = requests.get(url)
    return response.status_code == 200

spark_version=3.3
url = f"https://raw.githubusercontent.com/microsoft/synapse-spark-runtime/main/Fabric/spark{spark_version}/Components.json"
subsystem = "fabricPython"

# Fetch the URL content
response = requests.get(url)

# Initialize data to avoid reference before assignment error
data = {}

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON content
    json_data = json.loads(response.text)
    data = json_data["components"]
else:
    print(f"Failed to fetch the URL: {response.status_code}")

# Extract information
packages = data.get(subsystem, [])

# Open the requirements.txt file in write mode
with open('/workspace/docker/build/versions/requirements.txt', 'a') as file:
    for package in packages:
        # Check if the package and version exist on PyPI
        if package_exists_on_pypi(package['Name'], package['Current']):
            # Write the package and its version to the file
            print(f"{package['Name']}=={package['Current']}\n")
            file.write(f"{package['Name']}=={package['Current']}\n")
        else:
            pass
            #print(f"Package {package['Name']}=={package['Current']} not found on PyPI, skipping...")

