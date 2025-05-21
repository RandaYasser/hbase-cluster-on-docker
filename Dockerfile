FROM ubuntu:22.04

RUN apt update && apt upgrade -y && \
    apt install -y openjdk-8-jdk ssh vim sudo netcat 


RUN adduser --disabled-password --gecos "" hadoop && \
    echo "hadoop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Download and extract Hadoop and ZooKeeper in one layer
ADD https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz /tmp/hadoop.tar.gz 
ADD https://archive.apache.org/dist/zookeeper/zookeeper-3.6.3/apache-zookeeper-3.6.3-bin.tar.gz /tmp/zookeeper.tar.gz 


RUN tar -xzf /tmp/hadoop.tar.gz && \
    tar -xzf /tmp/zookeeper.tar.gz && \
    mv apache-zookeeper-3.6.3-bin /usr/local/zookeeper && \
    mv hadoop-3.3.6 /usr/local/hadoop && \
    rm -rf /tmp/hadoop.tar.gz /tmp/zookeeper.tar.gz 

# Create directories and set permissions
RUN mkdir -p /hadoop/dfs/name /hadoop/dfs/data /hadoop/dfs/journal /usr/local/hadoop/tmpdata /usr/local/zookeeper/data && \
    chown -R hadoop:hadoop /usr/local/zookeeper /usr/local/hadoop /hadoop/dfs/

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 \
    HADOOP_HOME=/usr/local/hadoop \
    HADOOP_INSTALL=/usr/local/hadoop \
    HADOOP_MAPRED_HOME=/usr/local/hadoop \
    HADOOP_COMMON_HOME=/usr/local/hadoop \
    HADOOP_HDFS_HOME=/usr/local/hadoop \
    HADOOP_YARN_HOME=/usr/local/hadoop \
    HADOOP_COMMON_LIB_NATIVE_DIR=/usr/local/hadoop/lib/native \
    PATH="$PATH:/usr/local/hadoop/bin:/usr/local/hadoop/sbin:/usr/local/zookeeper/bin" \
    HADOOP_OPTS="-Djava.library.path=/usr/local/hadoop/lib/native"

    
# Copy configuration files
COPY config/hadoop/* /usr/local/hadoop/etc/hadoop/
COPY config/zookeeper/* /usr/local/zookeeper/conf/

COPY start_hadoop.sh /start_hadoop.sh
RUN chmod +x /start_hadoop.sh
RUN mkdir /code && \
    chmod -R 777 /code && \
    chown -R hadoop:hadoop /code && \
    mkdir /data && \
    chmod -R 777 /data && \
    chown -R hadoop:hadoop /data && \
    mkdir -p /etc/security/keytabs/



# Switch to hadoop user and set up SSH
USER hadoop
WORKDIR /home/hadoop/

RUN mkdir -p /home/hadoop/.ssh && \
    ssh-keygen -t rsa -N "" -f /home/hadoop/.ssh/id_rsa && \
    cat /home/hadoop/.ssh/id_rsa.pub >> /home/hadoop/.ssh/authorized_keys && \
    chmod 600 /home/hadoop/.ssh/authorized_keys

# Set entrypoint
ENTRYPOINT ["/start_hadoop.sh"]
