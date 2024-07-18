FROM python:3.10

# Set environment variables
ENV JAVA_HOME=/opt/java/openjdk \
    PATH="${JAVA_HOME}/bin:${PATH}" \
    PIPENV_VENV_IN_PROJECT=1

ARG PYTHON_VERSION
ARG SPARK_VERSION
ARG DELTA_VERSION
ARG HADOOP_VERSION
ARG HIVE_VERSION
ARG LIVY_VERSION
ARG DERBY_VERSION

COPY --from=eclipse-temurin:8-jre $JAVA_HOME $JAVA_HOME
# Install dependencies and cleanup in a single layer
RUN apt-get update && apt-get -y upgrade && apt-get -y install tree \
    && python -m pip install --upgrade pip \
    && pip install --no-cache-dir pipenv \
    && rm -rf /var/lib/apt/lists/*

# Handle Python dependencies
ADD requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Combine apt-get update, installations, and cleanup into a single RUN to reduce layers
RUN apt-get update && apt-get install -y \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Set Home Directories
ENV SPARK_HOME="/opt/spark"
ENV HIVE_HOME="/opt/hive"
ENV HADOOP_HOME="/opt/hadoop"

#mkdir
RUN mkdir -p $SPARK_HOME && mkdir -p $HADOOP_HOME && mkdir -p $HIVE_HOME

#############################################
# install spark
############################################

RUN wget --verbose "https://archive.apache.org/dist/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop$(echo $HADOOP_VERSION | cut -d '.' -f1).tgz" -O /tmp/spark.tgz && \
        tar -xf /tmp/spark.tgz -C $SPARK_HOME --strip-components=1 && \
        rm /tmp/spark.tgz; 

# SET SPARK ENV VARIABLES
ENV PATH="${SPARK_HOME}/bin/:${PATH}:${SPARK_HOME}/tmp/ivy2/jars" \
    SPARK_HOME="${SPARK_HOME}" \
    SPARK_CONF_DIR="${SPARK_HOME}/conf" \
    SPARK_DIST_CLASSPATH="${SPARK_HOME}/jars/*" \
    SPARK_EXTRA_CLASSPATH="$SPARK_CLASSPATH:${SPARK_HOME}/tmp/ivy2/jars/*" \
    SPARK_CLASSPATH="$SPARK_CLASSPATH:$SPARK_EXTRA_CLASSPATH:$HADOOP_PREFIX/etc/hadoop" \
    SPARK_PUBLIC_DNS=localhost

# Fix Spark installation for Java 11 and Apache Arrow library
# see: https://github.com/apache/spark/pull/27356, https://spark.apache.org/docs/latest/#downloading
RUN cp -p "${SPARK_HOME}/conf/spark-defaults.conf.template" "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.driver.extraJavaOptions -Dio.netty.tryReflectionSetAccessible=true' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.executor.extraJavaOptions -Dio.netty.tryReflectionSetAccessible=true' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo "spark.jars.packages org.apache.spark:spark-hive_2.12:3.1.2,org.apache.hadoop:hadoop-azure-datalake:3.0.0-alpha1,com.microsoft.azure:azure-storage:8.6.3,io.delta:delta-core_2.12:$DELTA_VERSION,org.apache.hadoop:hadoop-azure:${HADOOP_VERSION},com.azure:azure-storage-blob:12.25.2" >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.serializer org.apache.spark.serializer.KryoSerializer' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.catalog.spark_catalog org.apache.spark.sql.delta.catalog.DeltaCatalog'  >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.extensions io.delta.sql.DeltaSparkSessionExtension' >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.jars.ivy ${SPARK_HOME}/tmp/ivy2" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.warehouse.dir /user/hive/warehouse" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.catalogImplementation hive" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.execution.arrow.pyspark.enabled true" >> "${SPARK_HOME}/conf/spark-defaults.conf"


###########################################
# Install Hive
###########################################

RUN if [ -n "$HIVE_VERSION" ]; then \
        wget  --verbose "https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz" -O /tmp/hive.tar.gz && \
        tar -xf /tmp/hive.tar.gz -C /opt/hive && \
        rm /tmp/hive.tar.gz; \
    fi

# SET HIVE ENV VARIABLES
ENV HIVE_HOME=/opt/hive
ENV HIVE_CONF_DIR=$HIVE_HOME/conf
ENV PATH=$HIVE_HOME/sbin:$HIVE_HOME/bin:$PATH
COPY hive/conf/hive-site.xml $HIVE_CONF_DIR/

ENV SPARK_CLASSPATH="$SPARK_CLASSPATH:$HIVE_HOME/lib/"

COPY hive/conf/hive-site.xml $SPARK_HOME/conf/hive-site.xml

# RUN set -x \
#  && curl -fsSL https://archive.apache.org/dist/hive/KEYS -o /tmp/hive-KEYS  \
#  && gpg --import /tmp/hive-KEYS \
#  && mkdir $HIVE_HOME \
#  && curl -fsSL $HIVE_URL -o /tmp/hive.tar.gz \
#  && curl -fsSL $HIVE_URL.asc -o /tmp/hive.tar.gz.asc \
#  && gpg --verify /tmp/hive.tar.gz.asc \
#  && tar -xf /tmp/hive.tar.gz -C $HIVE_HOME --strip-components 1 \
#  && rm /tmp/hive*


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
    YARN_CONF_DIR=$HADOOP_PREFIX/etc/hadoop \
    HADOOP_CLASSPATH="$HADOOP_HOME/share/hadoop/tools/lib/*"

# Set SPARK CLASSPATH
RUN echo 'export SPARK_DIST_CLASSPATH="$($HADOOP_HOME/bin/hadoop classpath:${SPARK_HOME}/tmp/ivy2)"' >> /etc/environment
ENV SPARK_EXTRA_CLASSPATH="$SPARK_CLASSPATH:$${SPARK_HOME}/tmp/ivy2/jars/*"
ENV SPARK_CLASSPATH="$SPARK_CLASSPATH:$HADOOP_CLASSPATH:$SPARK_EXTRA_CLASSPATH"

# Set Default Environment Variables in HADOOP ENV.sh
RUN sed -i '/^export JAVA_HOME/ s:.*:export JAVA_HOME=/usr/java/default\nexport HADOOP_PREFIX=$HADOOP_HOME\nexport HADOOP_HOME=$HADOOP_HOME\n:' $HADOOP_PREFIX/etc/hadoop/hadoop-env.sh
RUN sed -i '/^export HADOOP_CONF_DIR/ s:.*:export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop/:' $HADOOP_PREFIX/etc/hadoop/hadoop-env.sh

RUN mkdir $HADOOP_PREFIX/input && \
     cp $HADOOP_PREFIX/etc/hadoop/*.xml $HADOOP_PREFIX/input

# Install ssh and supervisor, setup SSH keys, and configure known hosts in one RUN command
RUN apt-get update && apt-get install -y ssh supervisor && \
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

RUN echo 'export SPARK_DIST_CLASSPATH="$($HADOOP_HOME/bin/hadoop classpath:${SPARK_HOME}/tmp/ivy2:$HIVE_HOME/lib classpath)"' >> /etc/environment

RUN for f in ${SPARK_HOME}/jars/*.jar; do \
        CLASSPATH=${CLASSPATH}:$f; \
    done

    
ENV HADOOP_CLASSPATH="$HADOOP_CLASSPATH:$HIVE_HOME/lib/*"

ENV SPARK_CLASSPATH="$SPARK_CLASSPATH:$HADOOP_CLASSPATH"

###########################################
# Install Derby
###########################################

#SET ENV Variables
ENV DERBY_HOME /opt/derby \
    PATH $PATH:$DERBY_HOME/bin

# Download and install Derby
RUN wget --verbose "http://apache.mirrors.pair.com/db/derby/db-derby-$DERBY_VERSION/db-derby-$DERBY_VERSION-bin.tar.gz" -O /tmp/derby.tar.gz \
    && mkdir -p "$DERBY_HOME" \
    && tar -xzf /tmp/derby.tar.gz -C "$DERBY_HOME" --strip-components=1 \
    && rm /tmp/derby.tar.gz

###########################################
# Install Apache Livy
###########################################

#Set Livy variables
ENV LIVY_PORT=8998 \
    LIVY_HOME=/opt/livy \
    LIVY_CONF_DIR="${LIVY_HOME}/conf"

RUN curl --progress-bar -L --retry 3 \
    "https://archive.apache.org/dist/incubator/livy/${LIVY_VERSION}/apache-livy-${LIVY_VERSION}_2.12-bin.zip" \
    -o "/tmp/apache-livy-${LIVY_VERSION}_2.12-bin.zip" \
  && unzip -qq "/tmp/apache-livy-${LIVY_VERSION}_2.12-bin.zip" -d /tmp/ \
  && mv /tmp/apache-livy-${LIVY_VERSION}_2.12-bin ${LIVY_HOME} \
  && rm "/tmp/apache-livy-${LIVY_VERSION}_2.12-bin.zip" \
  && mkdir "${LIVY_HOME}/logs" \
  && chown -R root:root "${LIVY_HOME}"

COPY livy/conf/livy.conf /usr/livy/conf/livy.conf

HEALTHCHECK CMD curl -f "http://host.docker.internal:${LIVY_PORT}/" || exit 1

###########################################
# Install Python & Spark dependencies
###########################################

# Install pyspark and delta-spark using pip
RUN pip install --no-cache-dir pyspark==${SPARK_VERSION} delta-spark==$DELTA_VERSION ipykernel

#Install Spark dependencies by running Spark once
RUN python -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.getOrCreate(); spark.stop()"  && python -m spylon_kernel install

#ADD Spark IVY jars to the CLASSPATH
RUN for f in ${SPARK_HOME}/tmp/ivy2/jars/*.jar; do \
        CLASSPATH=${CLASSPATH}:$f; \
    done

COPY sparkmagic/example_config.json /home/root/.sparkmagic/config.json

# Setup directories, configure Sparkmagic, and install Jupyter kernels in a single RUN to reduce layers
RUN mkdir -p /home/root/.sparkmagic && \
    sed -i 's/localhost/spark/g' /home/root/.sparkmagic/config.json && \
    jupyter nbextension enable --py --sys-prefix widgetsnbextension && \
    KERNELS_LOCATION=$(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels && \
    jupyter-kernelspec install --user ${KERNELS_LOCATION}/sparkkernel && \
    jupyter-kernelspec install --user ${KERNELS_LOCATION}/pysparkkernel && \
    jupyter-kernelspec install --user ${KERNELS_LOCATION}/sparkrkernel && \
    jupyter serverextension enable --py sparkmagic

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

# MapReduce JobHistory Server ports
EXPOSE 10020 19888

#Additional ports for specific needs (e.g., SSH, custom applications)
EXPOSE 2122 49707

# Apache Livy Port
EXPOSE 8998

# USER root

RUN echo 'export PATH=$PATH:$HADOOP_PREFIX/bin:$SPARK_HOME/bin:$HIVE_HOME/bin' >> ~/.bashrc

# Clean up temporary files
RUN rm -rf /tmp/*

ADD bootstrap.sh /etc/bootstrap.sh

CMD ["bash","/etc/bootstrap.sh"]