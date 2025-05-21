#!/bin/bash

sudo service ssh start
if [ "$NODE_TYPE" == "master" ] ; then
    hbase master start
else
    hdfs --daemon start datanode
    yarn --daemon start nodemanager
    hbase-daemon.sh start regionserver
fi
jps
tail -f /dev/null