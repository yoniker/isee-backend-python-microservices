aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 360816483914.dkr.ecr.us-east-1.amazonaws.com
docker build -t isee_proxy .
docker tag isee_proxy:latest 360816483914.dkr.ecr.us-east-1.amazonaws.com/isee_proxy:latest
docker push 360816483914.dkr.ecr.us-east-1.amazonaws.com/isee_proxy:latest