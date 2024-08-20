# ARG PYTHON_VERSION
# ARG JAVA_VERSION
# FROM dependencies:latest AS dependencies
ARG PYTHON_VERSION
ARG JAVA_VERSION
FROM eclipse-temurin:${JAVA_VERSION}-jre as java-jre

ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim AS base
ARG PYTHON_VERSION
ARG JAVA_VERSION

# Set environment variables
ENV JAVA_HOME=/opt/java/openjdk \
    PATH="${JAVA_HOME}/bin:${PATH}" \
    PIPENV_VENV_IN_PROJECT=1 \
    HDFS_NAMENODE_USER=root \
    HDFS_DATANODE_USER=root \ 
    HDFS_SECONDARYNAMENODE_USER=root

#Set Livy variables
ENV LIVY_PORT=8998 \
    LIVY_HOME=/opt/livy \
    LIVY_CONF_DIR="${LIVY_HOME}/conf"

ARG SPARK_VERSION
ARG SCALA_VERSION
ARG DELTA_VERSION
ARG HADOOP_VERSION
ARG HIVE_VERSION
ARG LIVY_VERSION
ARG DERBY_VERSION
ARG KYUUBI_VERSION

COPY ./artifacts /tmp/

# Local Build steps to directly copy the tar archives, commented out by default because of disk size limit on github actions.
# COPY --from=dependencies /artifacts /tmp

# Extract the tar archives
RUN tar -xzf /tmp/python-packages.tar.gz -C /usr/local/lib/python${PYTHON_VERSION} && \
    tar -xzf /tmp/bin.tar.gz -C /usr/local/ && \
    tar -xzf /tmp/livy.tar.gz -C /opt/ && \
    tar -xzf /tmp/share.tar.gz -C /usr/local/ && \
    tar -xzf /tmp/include.tar.gz -C /usr/local/

# Copy the Java Runtime Environment (JRE) from the eclipse-temurin image
COPY --from=java-jre $JAVA_HOME $JAVA_HOME

# Set Home Directories
ENV SPARK_HOME="/opt/spark"
ENV HIVE_HOME="/opt/hive"
ENV HADOOP_HOME="/opt/hadoop"
ENV KYUUBI_HOME="/opt/kyuubi"
# Set environment variables
ENV PYSPARK_PYTHON=/usr/local/bin/python${PYTHON_VERSION}
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python${PYTHON_VERSION}
RUN apt-get update && apt-get install -y wget curl procps
#mkdir
RUN mkdir -p $SPARK_HOME && mkdir -p $HADOOP_HOME && mkdir -p $HIVE_HOME


# #############################################
# # install spark
# ############################################

# Conditional URL construction based on Scala and Spark versions
RUN if [ "$SCALA_VERSION" = "2.13" ] && [ "$(printf '%s\n' "$SPARK_VERSION" "4.0.0" | sort -V | head -n1)" != "4.0.0" ]; then \
        wget --verbose "https://archive.apache.org/dist/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop$(echo $HADOOP_VERSION | cut -d '.' -f1)-scala$SCALA_VERSION.tgz" -O /tmp/spark.tgz; \
    else \
        wget --verbose "https://archive.apache.org/dist/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop$(echo $HADOOP_VERSION | cut -d '.' -f1).tgz" -O /tmp/spark.tgz; \
    fi && \
    tar -xf /tmp/spark.tgz -C $SPARK_HOME --strip-components=1 && \
    rm /tmp/spark.tgz;

# SET SPARK ENV VARIABLES
ENV PATH="${SPARK_HOME}/bin/:${PATH}:${SPARK_HOME}/tmp/ivy2/jars" \
    SPARK_HOME="${SPARK_HOME}" \
    SPARK_CONF_DIR="${SPARK_HOME}/conf" \
    SPARK_EXTRA_CLASSPATH="${SPARK_HOME}/tmp/ivy2/jars/*" \
    SPARK_CLASSPATH="${SPARK_HOME}/jars/*" \
    SPARK_PUBLIC_DNS=localhost

# Fix Spark installation for Java 11 and Apache Arrow library
# see: https://github.com/apache/spark/pull/27356, https://spark.apache.org/docs/latest/#downloading
RUN cp -p "${SPARK_HOME}/conf/spark-defaults.conf.template" "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.driver.extraJavaOptions -Dio.netty.tryReflectionSetAccessible=true' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.executor.extraJavaOptions -Dio.netty.tryReflectionSetAccessible=true' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.serializer org.apache.spark.serializer.KryoSerializer' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.catalog.spark_catalog org.apache.spark.sql.delta.catalog.DeltaCatalog'  >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.hive.metastore.uris thrift://127.0.0.1:9083'  >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.extensions io.delta.sql.DeltaSparkSessionExtension' >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo 'spark.hive.metastore.schema.verification false' >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo 'hive.metastore.schema.verification false' >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.jars.ivy ${SPARK_HOME}/jars" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.warehouse.dir /user/hive/warehouse" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.catalogImplementation hive" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.execution.arrow.pyspark.enabled true" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.execution.arrow.pyspark.fallback.enabled true" >> "${SPARK_HOME}/conf/spark-defaults.conf"

# Dynamically set delta package based on DELTA_VERSION
RUN if [ "$(printf '3\n%s' "$DELTA_VERSION" | sort -V | head -n1)" = "3" ]; then \
        DELTA_PACKAGE="io.delta:delta-spark_${SCALA_VERSION}:$DELTA_VERSION"; \
    else \
        DELTA_PACKAGE="io.delta:delta-core_${SCALA_VERSION}:$DELTA_VERSION"; \
    fi && \
    echo "spark.jars.packages org.apache.spark:spark-hive_${SCALA_VERSION}:${HIVE_VERSION},org.apache.hadoop:hadoop-azure-datalake:3.0.0-alpha1,com.microsoft.azure:azure-storage:8.6.3,$DELTA_PACKAGE,org.apache.hadoop:hadoop-azure:${HADOOP_VERSION},com.azure:azure-storage-blob:12.25.2" >> "${SPARK_HOME}/conf/spark-defaults.conf"

###########################################
# Install Hive
###########################################

RUN if [ -n "$HIVE_VERSION" ]; then \
        wget  --verbose "https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz" -O /tmp/hive.tar.gz && \
        tar -xf /tmp/hive.tar.gz -C /opt/hive --strip-components=1 && \
        rm /tmp/hive.tar.gz; \
    fi

# SET HIVE ENV VARIABLES
ENV HIVE_HOME=/opt/hive \
    HIVE_CONF_DIR=$HIVE_HOME/conf \
    PATH=$HIVE_HOME/sbin:$HIVE_HOME/bin:$PATH \
    HIVE_CLASSPATH=$HIVE_HOME/lib/*

COPY hive/conf/ $HIVE_CONF_DIR/

ENV SPARK_CLASSPATH="$SPARK_CLASSPATH"

COPY hive/conf/ $SPARK_HOME/conf/

#############################################
# install HADOOP
############################################

RUN if [ -n "$HADOOP_VERSION" ]; then \
        wget --verbose "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" -O /tmp/hadoop.tar.gz && \
        tar -xf /tmp/hadoop.tar.gz -C $HADOOP_HOME --strip-components=1 && \
        rm /tmp/hadoop.tar.gz; \
    fi

# SET HADOOP ENV VARIABLES
ENV HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native \
    HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib" \
    HADOOP_OPTS="-Djava.library.path=$HADOOP_COMMON_LIB_NATIVE_DIR" \
    LD_LIBRARY_PATH="$HADOOP_HOME/lib/native" \
    PATH="$HADOOP_HOME/bin:$PATH" \
    HADOOP_PREFIX="$HADOOP_HOME" \
    HADOOP_COMMON_HOME="$HADOOP_PREFIX" \
    HADOOP_COMMON_LIB_NATIVE_DIR="$HADOOP_PREFIX/lib/native" \
    HADOOP_CONF_DIR="$HADOOP_PREFIX/etc/hadoop" \
    JAVA_LIBRARY_PATH="$HADOOP_HOME/lib/native:$JAVA_LIBRARY_PATH" \
    HADOOP_PREFIX=$HADOOP_HOME \
    HADOOP_COMMON_HOME=$HADOOP_HOME \
    HADOOP_HDFS_HOME=$HADOOP_HOME \
    HADOOP_MAPRED_HOME=$HADOOP_HOME \
    HADOOP_YARN_HOME=$HADOOP_HOME \
    HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop \
    YARN_CONF_DIR=$HADOOP_PREFIX/etc/hadoop

# Set Default Environment Variables in HADOOP ENV.sh
RUN sed -i '/^export JAVA_HOME/ s:.*:export JAVA_HOME=/usr/java/default\nexport HADOOP_PREFIX=$HADOOP_HOME\nexport HADOOP_HOME=$HADOOP_HOME\n:' $HADOOP_PREFIX/etc/hadoop/hadoop-env.sh
RUN sed -i '/^export HADOOP_CONF_DIR/ s:.*:export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop/:' $HADOOP_PREFIX/etc/hadoop/hadoop-env.sh

RUN mkdir $HADOOP_PREFIX/input && \
     cp $HADOOP_PREFIX/etc/hadoop/*.xml $HADOOP_PREFIX/input

# Install ssh and supervisor, setup SSH keys, and configure known hosts in one RUN command
RUN apt-get update && apt-get install -y ssh supervisor sudo && \
    mkdir /var/run/sshd && \
    ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 0600 ~/.ssh/authorized_keys && \
    /usr/sbin/sshd && \
    ssh-keyscan -H localhost >> /root/.ssh/known_hosts && \
    ssh-keyscan -H 127.0.0.1 >> /root/.ssh/known_hosts && \
    rm -rf /var/lib/apt/lists/* # Clean up apt cache to reduce image size


#ADD Hadoop configuration files
COPY hadoop/conf/*.xml $HADOOP_PREFIX/etc/hadoop/

#ADDitionally, copy to /etc/hadoop for global settings if necessary
COPY hadoop/conf/*.xml /etc/hadoop/

# Combine directory creation steps to reduce layers
RUN mkdir -p /data/yarn/nodemanager/log /data/yarn/nodemanager/data /data/hdfs/datanode /data/hdfs/namenode /data/transfert

#ADD Hadoop slave configuration
COPY hadoop/conf/slaves $HADOOP_PREFIX/etc/hadoop/slaves

# Formats the HDFS namenode, initializing the directory structure and metadata for HDFS. This is a necessary step for setting up a new Hadoop cluster.
RUN $HADOOP_PREFIX/bin/hdfs namenode -format

# workaround docker.io build error
RUN ls -la $HADOOP_HOME/etc/hadoop/*-env.sh && \
    chmod +x $HADOOP_HOME/etc/hadoop/*-env.sh && \
    ls -la $HADOOP_HOME/etc/hadoop/*-env.sh

# Combine directory creation steps to reduce layers
RUN mkdir -p /data/yarn/nodemanager/log /data/yarn/nodemanager/data /data/hdfs/datanode /data/hdfs/namenode /data/transfert

#ADD Hadoop slave configuration
COPY hadoop/conf/slaves $HADOOP_PREFIX/etc/hadoop/slaves

# Combine setting environment variables and modifying .bashrc in a single RUN to reduce layers
RUN echo 'export JAVA_HOME=/opt/java/openjdk' >> ~/.bashrc && \
    echo 'export HADOOP_OPTS="-Djava.library.path=$HADOOP_PREFIX/lib/native"' >> ~/.bashrc && \
    echo 'export HADOOP_OPTIONAL_TOOLS=hadoop-azure,hadoop-azure-datalake' >> ~/.bashrc

# Set HADOOP_OPTS as an environment variable for immediate effect in Docker layers
ENV HADOOP_OPTS="-Djava.library.path=$HADOOP_PREFIX/lib/native"

###########################################
# Install Derby
###########################################

#SET ENV Variables
ENV DERBY_HOME=/opt/derby \
    PATH=$PATH:$DERBY_HOME/bin \
    DERBY_CLASSPATH=$DERBY_HOME/lib/* \
    HADOOP_CLASSPATH="/opt/hadoop/etc/hadoop:/opt/hadoop/share/hadoop/common/lib/*:/opt/hadoop/share/hadoop/common/*:/opt/hadoop/share/hadoop/tools/lib/azure-data-lake-store-sdk-2.3.9.jar:/opt/hadoop/share/hadoop/tools/lib/wildfly-openssl-1.0.7.Final.jar:/opt/hadoop/share/hadoop/tools/lib/hadoop-azure-datalake-3.3.4.jar:/opt/hadoop/share/hadoop/hdfs:/opt/hadoop/share/hadoop/hdfs/lib/*:/opt/hadoop/share/hadoop/hdfs/*:/opt/hadoop/share/hadoop/mapreduce/*:/opt/hadoop/share/hadoop/yarn:/opt/hadoop/share/hadoop/yarn/lib/*:/opt/hadoop/share/hadoop/yarn/*"

# Download and install Derby
RUN wget --verbose "https://archive.apache.org/dist/db/derby/db-derby-$DERBY_VERSION/db-derby-$DERBY_VERSION-bin.tar.gz" -O /tmp/derby.tar.gz \
    && mkdir -p "$DERBY_HOME" \
    && tar -xzf /tmp/derby.tar.gz -C "$DERBY_HOME" --strip-components=1 \
    && rm /tmp/derby.tar.gz

###########################################
# Install Kyuubi
###########################################

# Download and extract Kyuubi
RUN wget "https://archive.apache.org/dist/kyuubi/kyuubi-$KYUUBI_VERSION/apache-kyuubi-$KYUUBI_VERSION-bin.tgz" && \
    tar -xzf "apache-kyuubi-$KYUUBI_VERSION-bin.tgz" && \
    mv "apache-kyuubi-$KYUUBI_VERSION-bin" "$KYUUBI_HOME" && \
    rm "apache-kyuubi-$KYUUBI_VERSION-bin.tgz"

# Create configuration directory and add kyuubi-defaults.conf
RUN mkdir -p "$KYUUBI_HOME/conf" && \
    echo "kyuubi.engine.type=spark" > ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.engine.spark.version=${SPARK_VERSION}" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.engine.spark.home=${SPARK_HOME}" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.frontend.bind.host=0.0.0.0" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.frontend.thrift.binary.bind.host=0.0.0.0" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.frontend.thrift.http.bind.host=0.0.0.0" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.frontend.mysql.bind.host=0.0.0.0" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.frontend.trino.bind.host=0.0.0.0" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.frontend.rest.bind.host=0.0.0.0" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf && \
    echo "kyuubi.engine.type=SPARK_SQL" >> ${KYUUBI_HOME}/conf/kyuubi-defaults.conf


###########################################
# Install Python & Spark dependencies
###########################################

#Install Spark dependencies by running Spark once
RUN python -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.getOrCreate(); spark.stop()"  && python -m spylon_kernel install

COPY sparkmagic/example_config.json /home/root/.sparkmagic/config.json

# Setup directories, configure Sparkmagic, and install Jupyter kernels in a single RUN to reduce layers
RUN mkdir -p /home/root/.sparkmagic && \
    sed -i 's/localhost/spark/g' /home/root/.sparkmagic/config.json && \
    jupyter nbextension enable --py --sys-prefix widgetsnbextension && \
    export KERNELS_LOCATION="$(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels" && \
    jupyter-kernelspec install ${KERNELS_LOCATION}/sparkkernel && \
    jupyter-kernelspec install ${KERNELS_LOCATION}/pysparkkernel && \
    jupyter-kernelspec install ${KERNELS_LOCATION}/sparkrkernel && \
    jupyter serverextension enable --py sparkmagic

# Conditionally remove Python 3.11 if PYTHON_VERSION is not 3.11
RUN if [ "$PYTHON_VERSION" != "3.11" ]; then \
    apt-get remove -y python3.11; \
    apt-get autoremove -y; \
    apt-get clean; \
    fi


###########################################
# Finalize
###########################################

#Install XML and JSON tools
RUN apt-get update && apt-get -y install xmlstarlet jq

#ADD and configure bootstrap script
COPY bootstrap.sh /etc/bootstrap.sh
RUN chown root:root /etc/bootstrap.sh && chmod 700 /etc/bootstrap.sh

# Hadoop NameNode, DataNode, Secondary NameNode, and other HDFS-related ports
EXPOSE 8020 50010 50020 50070 50075 50090

# YARN ResourceManager, NodeManager, and related ports
EXPOSE 8030 8031 8032 8033 8040 8042 8088

# Spark Master, Spark Worker (Executor), and Spark History Server ports
EXPOSE 7077 8080 18080

# Jupyter Notebook port
EXPOSE 8888

# Hive Metastore and `Kyuubi Thrift ports
EXPOSE 9083 10009

# MapReduce JobHistory Server ports
EXPOSE 10020 19888

#Additional ports for specific needs (e.g., SSH, custom applications)
EXPOSE 2122 49707

# Apache Livy Port
EXPOSE 8998

USER root

# Source the environment file to make the variable available
RUN set -a; source /etc/environment; set +a;

ENV PATH=$PATH:$HADOOP_PREFIX/bin:$SPARK_HOME/bin:$HIVE_HOME/bin:$DERBY_HOME/bin:$JAVA_HOME/bin \
    YARN_RESOURCEMANAGER_USER=root \
    YARN_NODEMANAGER_USER=root \
    JUPYTER_PATH=/usr/local/share/jupyter/kernels \
    HIVE_AUX_JARS_PATH=$HIVE_CLASSPATH:/opt/spark/lib/*:$DERBY_CLASSPATH:$HADOOP_CLASSPATH \
    SPARK_CLASSPATH=$SPARK_CLASSPATH:$HIVE_CLASSPATH \
    HADOOP_CLASSPATH=$HADOOP_CLASSPATH \
    SPARK_DIST_CLASSPATH=$HADOOP_CLASSPATH \
    CLASSPATH=$SPARK_CLASSPATH:$HIVE_CLASSPATH:$HADOOP_CLASSPATH:$DERBY_CLASSPATH:$TEZ_CLASSPATH

#Add Derby/Hive user
RUN useradd -s /bin/bash -m APP && \
    echo "APP:mine" | sudo chpasswd && \
    getent group hdfs > /dev/null || groupadd hdfs

RUN hdfs dfs -mkdir -p /user/hive/warehouse && \
    hdfs dfs -mkdir /user/root && \
    hdfs dfs -chown root:hdfs /user/root && \
    hdfs dfs -chown APP:hdfs /user/hive && \
    chmod -R 777 /opt/hive && \
    chmod -R 777 /opt/spark && \
    chmod -R 777 /opt/hadoop && \
    chmod -R 777 /tmp && \
    chmod -R 777 /user/hive && \
    chmod -R 777 /opt/derby && \
    mkdir -p /opt/hive/logs


# Make environment available to all users
RUN sh -c 'grep -qxF "session required pam_env.so" /etc/pam.d/common-session || echo "session required pam_env.so" >> /etc/pam.d/common-session' && \
    sh -c 'grep -qxF "session required pam_env.so" /etc/pam.d/common-session-noninteractive || echo "session required pam_env.so" >> /etc/pam.d/common-session-noninteractive' && \
    echo ". /etc/environment" >> /etc/profile && \
    echo 'while IFS= read -r line; do if [[ ! "$line" =~ ^# && ! -z "$line" ]]; then export "$line"; fi; done < /etc/environment' >> /etc/profile && \
    echo 'while IFS= read -r line; do if [[ ! "$line" =~ ^# && ! -z "$line" ]]; then export "$line"; fi; done < /etc/environment' >> /etc/bash.bashrc

    
# Clean up temporary files
RUN rm -rf /tmp/*

ADD bootstrap.sh /etc/bootstrap.sh

CMD ["bash","/etc/bootstrap.sh"]