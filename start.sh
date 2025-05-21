docker build -t hadoop-master .
docker build -f Dockerfile.hbase -t hadoop-hbase-image .
docker-compose up -d
