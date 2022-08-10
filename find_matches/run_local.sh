docker build . -t try
docker run -d  -it -p20002:20002/tcp try
