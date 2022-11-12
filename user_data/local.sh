docker build . -t user_data
docker run -d -it -p20003:20003/tcp -v /home/yoni/Projects/docker_services/user_data/keys:/home/user_data_service/keys user_data