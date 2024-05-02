FROM python:3.10
ENV JAVA_HOME=/opt/java/openjdk

ARG PYTHON_VERSION
ARG SPARK_VERSION
ARG DELTA_VERSION
ARG HADOOP_VERSION
ARG AZURE_STORAGE_ACCOUNTS

# HARDCODED VERSIONS
# ENV SPARK_VERSION=3.3.4 \
# HADOOP_VERSION=3 \
# JAVA_VERSION=11 \
#HADOOP_VERSION=3.3.4

COPY --from=eclipse-temurin:11-jre $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN java --version

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install tree
ENV PIPENV_VENV_IN_PROJECT=1

# ENV PIPENV_VENV_IN_PROJECT=1 is important: it causes the resuling virtual environment to be created as /app/.venv. Without this the environment gets created somewhere surprising, such as /root/.local/share/virtualenvs/app-4PlAip0Q - which makes it much harder to write automation scripts later on.

ADD requirements.txt /home/requirements.txt

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir pipenv
RUN pip install -r /home/requirements.txt

RUN rm /home/requirements.txt

#############################################
# install spark
############################################

# DOWNLOAD SPARK AND INSTALL
RUN DOWNLOAD_URL_SPARK="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" \
    && wget --verbose -O apache-spark.tgz  "${DOWNLOAD_URL_SPARK}"\
    && mkdir -p /home/spark \
    && tar -xf apache-spark.tgz -C /home/spark --strip-components=1 \
    && rm apache-spark.tgz

# SET SPARK ENV VARIABLES
ENV SPARK_HOME="/home/spark"
ENV PATH="${SPARK_HOME}/bin/:${PATH}:${SPARK_HOME}/tmp/ivy2/jars"
ENV HADOOP_HOME="/home/hadoop"

ENV SPARK_CLASSPATH="${SPARK_HOME}/jars/*"
ENV SPARK_EXTRA_CLASSPATH="$SPARK_CLASSPATH:${SPARK_HOME}/tmp/ivy2/jars/*"
ENV SPARK_CLASSPATH="$SPARK_CLASSPATH:$SPARK_EXTRA_CLASSPATH:$HADOOP_PREFIX/etc/hadoop"

# Fix Spark installation for Java 11 and Apache Arrow library
# see: https://github.com/apache/spark/pull/27356, https://spark.apache.org/docs/latest/#downloading
RUN cp -p "${SPARK_HOME}/conf/spark-defaults.conf.template" "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.driver.extraJavaOptions -Dio.netty.tryReflectionSetAccessible=true' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.executor.extraJavaOptions -Dio.netty.tryReflectionSetAccessible=true' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo "spark.jars.packages org.apache.hadoop:hadoop-azure-datalake:3.0.0-alpha1,com.microsoft.azure:azure-storage:8.6.3,io.delta:delta-core_2.12:$DELTA_VERSION,org.apache.hadoop:hadoop-azure:${HADOOP_VERSION},com.azure:azure-storage-blob:12.25.2" >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.serializer org.apache.spark.serializer.KryoSerializer' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.catalog.spark_catalog org.apache.spark.sql.delta.catalog.DeltaCatalog'  >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.extensions io.delta.sql.DeltaSparkSessionExtension' >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.jars.ivy ${SPARK_HOME}/tmp/ivy2" >> "${SPARK_HOME}/conf/spark-defaults.conf"

#############################################
# install HADOOP
############################################

RUN wget -O hadoop-${HADOOP_VERSION}.tar.gz https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    && mkdir -p /home/hadoop \
    && tar -xf hadoop-${HADOOP_VERSION}.tar.gz -C /home/hadoop --strip-components=1 \
    && rm hadoop-${HADOOP_VERSION}.tar.gz


ENV HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native \
    HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib" \
    HADOOP_OPTS="-Djava.library.path=$HADOOP_COMMON_LIB_NATIVE_DIR" \
    LD_LIBRARY_PATH="$HADOOP_HOME/lib/native" \
    PATH="$HADOOP_HOME/bin:$PATH" \
    HADOOP_PREFIX="$HADOOP_HOME" \
    HADOOP_COMMON_HOME="$HADOOP_PREFIX" \
    HADOOP_COMMON_LIB_NATIVE_DIR="$HADOOP_PREFIX/lib/native" \
    HADOOP_CONF_DIR="$HADOOP_PREFIX/etc/hadoop" \
    JAVA_LIBRARY_PATH="$HADOOP_HOME/lib/native:$JAVA_LIBRARY_PATH" 


ENV HADOOP_PREFIX /home/hadoop
ENV HADOOP_COMMON_HOME /home/hadoop
ENV HADOOP_HDFS_HOME /home/hadoop
ENV HADOOP_MAPRED_HOME /home/hadoop
ENV HADOOP_YARN_HOME /home/hadoop
ENV HADOOP_CONF_DIR /home/hadoop/etc/hadoop
ENV YARN_CONF_DIR $HADOOP_PREFIX/etc/hadoop

RUN echo 'export SPARK_DIST_CLASSPATH="$($HADOOP_HOME/bin/hadoop classpath:${SPARK_HOME}/tmp/ivy2)"' >> /etc/environment

ENV HADOOP_CLASSPATH="$HADOOP_HOME/share/hadoop/tools/lib/*"
ENV SPARK_EXTRA_CLASSPATH="$SPARK_CLASSPATH:$${SPARK_HOME}/tmp/ivy2/jars/*"
ENV SPARK_CLASSPATH="$SPARK_CLASSPATH:$HADOOP_CLASSPATH:$SPARK_EXTRA_CLASSPATH"


RUN sed -i '/^export JAVA_HOME/ s:.*:export JAVA_HOME=/usr/java/default\nexport HADOOP_PREFIX=/home/hadoop\nexport HADOOP_HOME=/home/hadoop\n:' $HADOOP_PREFIX/etc/hadoop/hadoop-env.sh
RUN sed -i '/^export HADOOP_CONF_DIR/ s:.*:export HADOOP_CONF_DIR=/home/hadoop/etc/hadoop/:' $HADOOP_PREFIX/etc/hadoop/hadoop-env.sh


RUN mkdir $HADOOP_PREFIX/input
RUN cp $HADOOP_PREFIX/etc/hadoop/*.xml $HADOOP_PREFIX/input


# install ssh and run through supervisor
RUN apt-get install -y ssh supervisor
RUN mkdir /var/run/sshd
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 0600 ~/.ssh/authorized_keys
RUN /usr/sbin/sshd && ssh-keyscan -H localhost >> /root/.ssh/known_hosts && ssh-keyscan -H 127.0.0.1 >> /root/.ssh/known_hosts



# pseudo distributed
ADD hadoop/conf/core-site.xml $HADOOP_PREFIX/etc/hadoop/core-site.xml

ADD hadoop/conf/hdfs-site.xml $HADOOP_PREFIX/etc/hadoop/hdfs-site.xml

ADD hadoop/conf/mapred-site.xml $HADOOP_PREFIX/etc/hadoop/mapred-site.xml

ADD hadoop/conf/yarn-site.xml $HADOOP_PREFIX/etc/hadoop/yarn-site.xml

ADD hadoop/conf/core-site.xml /etc/hadoop/core-site.xml
ADD hadoop/conf/yarn-site.xml /etc/hadoop/yarn-site.xml
ADD hadoop/conf/mapred-site.xml /etc/hadoop/mapred-site.xml
ADD hadoop/conf/hdfs-site.xml $HADOOP_PREFIX/etc/hadoop/hdfs-site.xml
ADD hadoop/conf/capacity-scheduler.xml /etc/hadoop/capacity-scheduler.xml
RUN mkdir -p /data/yarn/nodemanager/log /data/yarn/nodemanager/data /data/hdfs/datanode /data/hdfs/namenode
RUN mkdir -p /data/transfert


# slave management
ADD hadoop/conf/slaves $HADOOP_PREFIX/etc/hadoop/slaves

RUN $HADOOP_PREFIX/bin/hdfs namenode -format

# workaround docker.io build error
RUN ls -la /home/hadoop/etc/hadoop/*-env.sh && \
    chmod +x /home/hadoop/etc/hadoop/*-env.sh && \
    ls -la /home/hadoop/etc/hadoop/*-env.sh

ENV HDFS_NAMENODE_USER root
ENV HDFS_DATANODE_USER root
ENV HDFS_SECONDARYNAMENODE_USER root
ENV YARN_RESOURCEMANAGER_USER=root
ENV YARN_NODEMANAGER_USER=root
ENV YARN_PROXYSERVER_USER=root
###########################################
# Install Node JS for Sonarlint integration
###########################################

ENV NODE_VERSION=21.0.0
RUN apt install -y curl
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version
# Change the owner of the /root/.nvm directory to $UNAME
RUN chown -R root:root /root/.nvm
ENV PATH=$PATH:$HADOOP_PREFIX/bin:$SPARK_HOME/bin:$HIVE_HOME/bin:$ZEPPELIN_HOME/bin
###########################################
# Finalize
###########################################
# Set environment variables for new bash sessions, when starting Hadoop and Spark
RUN echo 'export JAVA_HOME=/opt/java/openjdk' >> ~/.bashrc
RUN echo 'export PATH=$PATH:$HADOOP_PREFIX/bin:$SPARK_HOME/bin:$HIVE_HOME/bin:$ZEPPELIN_HOME/bin' >> ~/.bashrc
RUN echo 'export HADOOP_OPTS="-Djava.library.path=$HADOOP_PREFIX/lib/native"' >> ~/.bashrc
ENV HADOOP_OPTS="-Djava.library.path=$HADOOP_PREFIX/lib/native"
RUN echo 'export HADOOP_OPTIONAL_TOOLS=hadoop-azure,hadoop-azure-datalake' >> ~/.bashrc

# configuration of supervisord

ADD bootstrap.sh /etc/bootstrap.sh
RUN chown root:root /etc/bootstrap.sh && \
    chmod 700 /etc/bootstrap.sh
    
# install data
VOLUME ["/data"]

# Expose ports
# hdfs port
EXPOSE 9000
EXPOSE 8020
# namenode port
EXPOSE 50070
# Resouce Manager
EXPOSE 8032
EXPOSE 8088
# MapReduce JobHistory Server Web UI
EXPOSE 19888
# MapReduce JobHistory Server
EXPOSE 10020
# Zeppelin
EXPOSE 8080

# Hdfs ports
EXPOSE 50010 50020 50070 50075 50090
# Mapred ports
EXPOSE 19888
#Yarn ports
EXPOSE 8030 8031 8032 8033 8040 8042 8088
#Other ports
EXPOSE 49707 2122   
# Spark submit, admin console, executor, history server
EXPOSE 7077 8080 65000 65001 65002 8085 8086 8087 18080

# Install pyspark and delta-spark using pip
RUN pip install --no-cache-dir pyspark==${SPARK_VERSION} delta-spark==$DELTA_VERSION ipykernel

RUN python -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.getOrCreate(); spark.stop()"

RUN apt-get -y install xmlstarlet jq

#loop through Azure Storage Accounts JSON Array and add the values in the HADOOP Config files
RUN echo $AZURE_STORAGE_ACCOUNTS | jq -c '.[]' | while read i; do \
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



ADD bootstrap.sh /etc/bootstrap.sh

CMD ["bash","/etc/bootstrap.sh"]