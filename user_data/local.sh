docker build . -t user_data
docker run -d -it -p20003:20003/tcp user_data
