aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 360816483914.dkr.ecr.us-east-1.amazonaws.com
docker build -t user_data .
docker tag user_data:latest 360816483914.dkr.ecr.us-east-1.amazonaws.com/user_data:latest
docker push 360816483914.dkr.ecr.us-east-1.amazonaws.com/user_data:latest