docker build . -t find_matches
docker run -d -it -p20002:20002/tcp find_matches