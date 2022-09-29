docker build . -t premium
docker run -d -it -p  20010:20010/tcp premium:latest