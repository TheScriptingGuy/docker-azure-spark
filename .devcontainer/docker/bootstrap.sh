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

export YARN_CONF_DIR=$HADOOP_PREFIX/etc

mkdir -p /tmp/spark/data
mkdir -p /tmp/hadoop/hdfs/tmp


# start ssh
/usr/sbin/sshd

bash $HADOOP_PREFIX/sbin/start-all.sh

bash $SPARK_HOME/sbin/start-all.sh

sleep infinity