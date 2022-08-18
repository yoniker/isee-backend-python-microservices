docker build . -t morpher
docker run -d -it -p20009:20009/tcp morpher:latest