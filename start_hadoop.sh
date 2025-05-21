#!/bin/bash

# Start SSH service
sudo service ssh start

if [ "$NODE_TYPE" == "master" ]; then
    
    echo "$NODE_NUM" | sudo tee /usr/local/zookeeper/data/myid
    /usr/local/zookeeper/bin/zkServer.sh start

    /usr/local/hadoop/bin/hdfs --daemon start journalnode

    if [ "$NODE_NUM" == "1" ]; then
        if [ ! -d /hadoop/dfs/name/current ]; then
            /usr/local/hadoop/bin/hdfs namenode -format -clusterid "hdcluster"
            /usr/local/hadoop/bin/hdfs namenode -initializeSharedEdits -force
            /usr/local/hadoop/bin/hdfs zkfc -formatZK
        fi
        # Start active NameNode
        /usr/local/hadoop/bin/hdfs --daemon start namenode
        /usr/local/hadoop/bin/hdfs --daemon start zkfc
        /usr/local/hadoop/bin/yarn --daemon start resourcemanager

    else
        # Wait for a while to ensure the active NameNode is up
        echo "Waiting for master1 NameNode..."
        until nc -zw 2 master1 8020; do
            sleep 5
            echo "Retrying connection to master1:8020..."
        done
        if [ ! -d /hadoop/dfs/name/current ]; then
            /usr/local/hadoop/bin/hdfs namenode -bootstrapStandby
        fi

        /usr/local/hadoop/bin/hdfs --daemon start namenode
        /usr/local/hadoop/bin/hdfs --daemon start zkfc
        /usr/local/hadoop/bin/yarn --daemon start resourcemanager
    fi

fi

jps  
# Keep container running
tail -f /dev/null
