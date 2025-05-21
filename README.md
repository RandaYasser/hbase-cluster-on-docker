# Hadoop-HBase Cluster with Docker

## Overview
This project sets up a fully distributed Hadoop and HBase cluster using Docker containers, featuring:
- 3-node Hadoop cluster with HDFS HA (NameNode + JournalNode + Zookeeper)
- 2-node HBase Master with automatic failover
- 3-node HBase RegionServers
- Integrated ZooKeeper ensemble for coordination

## Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended

## Quick Start
1. **Build images**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

2. **Access services**:
   - HDFS NameNode UI: http://localhost:19870
   - YARN ResourceManager: http://localhost:18088
   - HBase Master UI: http://localhost:16010

## Cluster Architecture
| Service          | Container Names  | Ports       |
|------------------|------------------|-------------|
| Hadoop NameNode  | master1-3        | 8020, 9870  |
| ZooKeeper        | master1-3        | 2181, 2888  |
| HBase Master     | hmaster1-2       | 16000, 16010|
| HBase RegionServer | regionserver1-3 | 16020, 16030|

## Key Features
✅ **High Availability**:
- Hadoop NameNode HA with ZooKeeper failover
- HBase Master automatic failover

✅ **Persistent Storage**:
- Dedicated volumes for HDFS (namenode/journalnode)
- ZooKeeper data persistence

✅ **Health Monitoring**:
- Built-in healthchecks for critical services
- Automatic container restart on failure

## Configuration Files
| File               | Purpose                          |
|--------------------|----------------------------------|
| `docker-compose.yml` | Cluster topology and networking |
| `start_hadoop.sh`  | Hadoop service initialization    |
| `start_hbase.sh`   | HBase service initialization     |

## Future Enhancements
- Add Kerberos authentication for communication between zookeeper and hbase
