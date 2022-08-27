docker build . -t analyze_user_fr
docker run -it -d -p20006:20006/tcp analyze_user_fr
