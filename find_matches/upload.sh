aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 360816483914.dkr.ecr.us-east-1.amazonaws.com
docker build . -t find_matches:19
docker tag find_matches:19 360816483914.dkr.ecr.us-east-1.amazonaws.com/find_matches:19
docker push 360816483914.dkr.ecr.us-east-1.amazonaws.com/find_matches:19