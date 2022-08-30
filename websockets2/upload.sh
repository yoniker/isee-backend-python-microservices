aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 360816483914.dkr.ecr.us-east-1.amazonaws.com
docker build -t websockets .
docker tag websockets:latest 360816483914.dkr.ecr.us-east-1.amazonaws.com/websockets:latest
docker push 360816483914.dkr.ecr.us-east-1.amazonaws.com/websockets:latest