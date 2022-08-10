docker build . -t analyze_user_fr
docker run -it -d -p20006:20006/tcp analyze_user_fr
sleep 5
curl "localhost:20006/analyze-user-fr/perform_analysis/5EX44AtZ5cXxW1O12G3tByRcC012"
