FROM python:3.10
ENV JAVA_HOME=/opt/java/openjdk

ARG PYTHON_VERSION
ARG SPARK_VERSION
ARG DELTA_VERSION
ARG HADOOP_VERSION

COPY --from=eclipse-temurin:8-jre $JAVA_HOME $JAVA_HOME
ENV PATH="${JAVA_HOME}/bin:${PATH}"

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
# install add sudo and add vsts user for Azure Devops Pipelines
############################################

# Install sudo
RUN apt-get update && apt-get install -y sudo

# Create the vsts_azpcontainer user if it doesn't already exist
# and add it to the sudo group with no password required for sudo commands
RUN useradd -m vsts_azpcontainer || true && \
    echo "vsts_azpcontainer ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

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
    echo "spark.jars.packages org.apache.spark:spark-hive_2.12:3.1.2,org.apache.hadoop:hadoop-azure-datalake:3.0.0-alpha1,com.microsoft.azure:azure-storage:8.6.3,io.delta:delta-core_2.12:$DELTA_VERSION,org.apache.hadoop:hadoop-azure:${HADOOP_VERSION},com.azure:azure-storage-blob:12.25.2" >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.serializer org.apache.spark.serializer.KryoSerializer' >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.catalog.spark_catalog org.apache.spark.sql.delta.catalog.DeltaCatalog'  >> "${SPARK_HOME}/conf/spark-defaults.conf" && \
    echo 'spark.sql.extensions io.delta.sql.DeltaSparkSessionExtension' >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.jars.ivy ${SPARK_HOME}/tmp/ivy2" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.warehouse.dir /user/hive/warehouse" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.catalogImplementation hive" >> "${SPARK_HOME}/conf/spark-defaults.conf" &&\
    echo "spark.sql.execution.arrow.pyspark.enabled true" >> "${SPARK_HOME}/conf/spark-defaults.conf"


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
# Finalize
###########################################
# Set environment variables for new bash sessions, when starting Hadoop and Spark
RUN echo 'export JAVA_HOME=/opt/java/openjdk' >> ~/.bashrc

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

RUN python -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.getOrCreate(); spark.stop()"  && python -m spylon_kernel install

RUN mkdir /home/root/
RUN mkdir /home/root/.sparkmagic
COPY sparkmagic/example_config.json /home/root/.sparkmagic/config.json
RUN sed -i 's/localhost/spark/g' /home/root/.sparkmagic/config.json
RUN jupyter nbextension enable --py --sys-prefix widgetsnbextension
RUN jupyter-kernelspec install --user $(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels/sparkkernel
RUN jupyter-kernelspec install --user $(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels/pysparkkernel
RUN jupyter-kernelspec install --user $(pip show sparkmagic | grep Location | cut -d" " -f2)/sparkmagic/kernels/sparkrkernel
RUN jupyter serverextension enable --py sparkmagic

ARG LIVY_VERSION=0.8.0-incubating
ENV LIVY_HOME /usr/livy
ENV LIVY_CONF_DIR "${LIVY_HOME}/conf"
ENV LIVY_PORT 8998

ARG HIVE_VERSION=3.1.2
ARG HIVE_URL=https://archive.apache.org/dist/hive/hive-$HIVE_VERSION/apache-hive-$HIVE_VERSION-bin.tar.gz
ENV HIVE_HOME=/opt/hive

RUN set -x \
 && curl -fsSL https://archive.apache.org/dist/hive/KEYS -o /tmp/hive-KEYS  \
 && gpg --import /tmp/hive-KEYS \
 && mkdir $HIVE_HOME \
 && curl -fsSL $HIVE_URL -o /tmp/hive.tar.gz \
 && curl -fsSL $HIVE_URL.asc -o /tmp/hive.tar.gz.asc \
 && gpg --verify /tmp/hive.tar.gz.asc \
 && tar -xf /tmp/hive.tar.gz -C $HIVE_HOME --strip-components 1 \
 && rm /tmp/hive*

ENV HIVE_CONF_DIR=$HIVE_HOME/conf
ENV PATH=$HIVE_HOME/sbin:$HIVE_HOME/bin:$PATH
COPY hive/conf/hive-site.xml $HIVE_CONF_DIR/

ENV SPARK_CLASSPATH="$SPARK_CLASSPATH:$HIVE_HOME/lib/"

###########################################
# Install Apache Livy
###########################################

RUN curl --progress-bar -L --retry 3 \
    "https://archive.apache.org/dist/incubator/livy/${LIVY_VERSION}/apache-livy-${LIVY_VERSION}_2.12-bin.zip" \
    -o "./apache-livy-${LIVY_VERSION}_2.12-bin.zip" \
  && ls . \
  && unzip -qq "./apache-livy-${LIVY_VERSION}_2.12-bin.zip" -d /usr \
  && mv "/usr/apache-livy-${LIVY_VERSION}_2.12-bin" "${LIVY_HOME}" \
  && rm -rf "./apache-livy-${LIVY_VERSION}_2.12-bin.zip" \
  && mkdir "${LIVY_HOME}/logs" \
  && chown -R root:root "${LIVY_HOME}"

EXPOSE 8998

HEALTHCHECK CMD curl -f "http://host.docker.internal:${LIVY_PORT}/" || exit 1

ENV SPARK_PUBLIC_DNS=localhost

RUN apt-get -y install xmlstarlet jq postgresql postgresql-contrib


RUN mkdir /home/postgres
RUN mkdir /home/postgres/data

RUN chown -R postgres:postgres /home/postgres

USER postgres

COPY hive/postgres/init.sql /home/postgres/init.sql

RUN /usr/lib/postgresql/15/bin/initdb -D /home/postgres/data

#RUN echo "include_if_exists = '/home/postgres/init.sql'" >> /home/postgres/data/postgresql.conf

EXPOSE 5432

USER root

RUN echo 'export PATH=$PATH:$HADOOP_PREFIX/bin:$SPARK_HOME/bin:$HIVE_HOME/bin' >> ~/.bashrc

ENV HADOOP_CLASSPATH="$HADOOP_CLASSPATH:$HIVE_HOME/lib/*"

ENV SPARK_CLASSPATH="$SPARK_CLASSPATH:$HADOOP_CLASSPATH"
ADD bootstrap.sh /etc/bootstrap.sh
COPY livy/conf/livy.conf /usr/livy/conf/livy.conf
COPY hive/conf/hive-site.xml $SPARK_HOME/conf/hive-site.xml
RUN wget https://jdbc.postgresql.org/download/postgresql-42.2.5.jar -O postgresql-42.2.5.jar
RUN cp ./postgresql-42.2.5.jar $HIVE_HOME/lib/
RUN cp ./postgresql-42.2.5.jar $SPARK_HOME/jars/
ENV CLASSPATH=$CLASSPATH:$HIVE_HOME/lib/postgresql-42.2.5.jar
RUN echo 'export SPARK_DIST_CLASSPATH="$($HADOOP_HOME/bin/hadoop classpath:${SPARK_HOME}/tmp/ivy2:$HIVE_HOME/lib classpath)"' >> /etc/environment

RUN for f in ${SPARK_HOME}/jars/*.jar; do \
        CLASSPATH=${CLASSPATH}:$f; \
    done
RUN for f in ${SPARK_HOME}/tmp/ivy2/jars/*.jar; do \
        CLASSPATH=${CLASSPATH}:$f; \
    done

CMD ["bash","/etc/bootstrap.sh"]