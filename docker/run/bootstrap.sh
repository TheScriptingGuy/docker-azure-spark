#!/bin/bash
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations

bash $HADOOP_PREFIX/etc/hadoop/hadoop-env.sh
bash $HADOOP_PREFIX/etc/hadoop/yarn-env.sh
bash $HADOOP_PREFIX/etc/hadoop/mapred-env.sh
bash $SPARK_HOME/conf/spark-env.sh
echo $HADOOP_OPTS

pip install -r /workspace/docker/run/requirements.txt

su -c "/usr/lib/postgresql/15/bin/pg_ctl start -D /home/postgres/data &" postgres
psql -U postgres -c "CREATE ROLE hive;"
psql -U postgres -c "CREATE USER hive WITH PASSWORD 'hive';"
psql -U postgres -c "GRANT postgres TO hive;"
psql -U postgres -c "CREATE DATABASE metastore;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metastore TO hive;"
psql -U postgres -c "ALTER ROLE hive WITH LOGIN PASSWORD 'hive';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON SCHEMA public TO hive;"
psql -U postgres -c "ALTER SCHEMA public OWNER TO postgres;"
psql -U postgres -c "GRANT USAGE, CREATE ON SCHEMA public TO hive;"
psql -U postgres -c "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hive;"

#loop through Azure Storage Accounts JSON Array and add the values in the HADOOP Config files
echo $AZURE_STORAGE_ACCOUNTS | jq -c '.[]' | while read i; do \
        AZURE_STORAGE_ACCOUNT_NAME=$(echo $i | jq -r '.StorageAccountName') && \
        AZURE_STORAGE_ACCOUNT_KEY=$(echo $i | jq -r '.StorageAccountKey') && \
        echo "Processing $AZURE_STORAGE_ACCOUNT_NAME with key $AZURE_STORAGE_ACCOUNT_KEY" && \
        xmlstarlet ed --inplace \
        --subnode "/configuration" --type elem -n propertyTMP \
        --subnode "//propertyTMP" --type elem -n name -v "fs.azure.account.key.${AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net" \
        --subnode "//propertyTMP" --type elem -n value -v "${AZURE_STORAGE_ACCOUNT_KEY}" \
        --rename "//propertyTMP" -v "property" \
        $HADOOP_HOME/etc/hadoop/core-site.xml && \
        xmlstarlet ed --inplace \
        --subnode "/configuration" --type elem -n propertyTMP \
        --subnode "//propertyTMP" --type elem -n name -v "fs.azure.account.key.${AZURE_STORAGE_ACCOUNT_NAME}.dfs.core.windows.net" \
        --subnode "//propertyTMP" --type elem -n value -v "${AZURE_STORAGE_ACCOUNT_KEY}" \
        --rename "//propertyTMP" -v "property" \
        $HADOOP_HOME/etc/hadoop/core-site.xml && \
        xmlstarlet ed --inplace \
        --subnode "/configuration" --type elem -n propertyTMP \
        --subnode "//propertyTMP" --type elem -n name -v "fs.azure.account.auth.type.${AZURE_STORAGE_ACCOUNT_NAME}.dfs.core.windows.net" \
        --subnode "//propertyTMP" --type elem -n value -v "SharedKey" \
        --rename "//propertyTMP" -v "property" \
        $HADOOP_HOME/etc/hadoop/core-site.xml; \
    done

export YARN_CONF_DIR=$HADOOP_PREFIX/etc

mkdir -p /tmp/spark/data
mkdir -p /tmp/hadoop/hdfs/tmp



if [ ! -f "$NAMEDIR"/initialized ]; then
  echo "Configuring Hive..."
  hdfs dfs -mkdir -p  /user/hive/warehouse
  schematool -dbType postgres -initSchema
  touch "$NAMEDIR"/initialized
fi

echo "Starting Hive Metastore..."
hive --service metastore > /home/root/hive-metastore.log 2>&1 &

echo "Starting Hive server2..."
hiveserver2 > /home/root/hive-server.log 2>&1 &
# Start Jupyter Notebook without a password
bash jupyter notebook --allow-root --NotebookApp.allow_origin='*' --NotebookApp.password='' --NotebookApp.token='' &
$LIVY_HOME/bin/livy-server &
# start ssh
/usr/sbin/sshd  &

bash $HADOOP_PREFIX/sbin/start-all.sh  &

bash $SPARK_HOME/sbin/start-all.sh  &


sleep infinity