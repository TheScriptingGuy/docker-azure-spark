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
while IFS= read -r line; do if [[ ! "$line" =~ ^# && ! -z "$line" ]]; then export "$line"; fi; done < /etc/environment | sed "s/\"//g"

nohup jupyter notebook --allow-root --NotebookApp.allow_origin='*' --NotebookApp.password='' --NotebookApp.token='' &

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

java -Dderby.drda.host=0.0.0.0 -jar $DERBY_HOME/lib/derbyrun.jar server start > ~/derby_server.log 2>&1 &
export YARN_CONF_DIR=$HADOOP_PREFIX/etc

mkdir -p /tmp/spark/data
mkdir -p /tmp/hadoop/hdfs/tmp

echo "Configuring Hive..."
schematool -dbType derby -initSchema


echo "Starting Hive Metastore..."
/opt/hive/bin/hive --service metastore --hiveconf hive.root.logger=INFO,console > /opt/hive/metastore.log 2>&1 &

$LIVY_HOME/bin/livy-server &

echo "Starting Kyuubi Server..."
/opt/kyuubi/bin/kyuubi start

# start ssh
/usr/sbin/sshd  &

bash $HADOOP_PREFIX/sbin/start-all.sh  &

bash $SPARK_HOME/sbin/start-all.sh  &

sleep infinity