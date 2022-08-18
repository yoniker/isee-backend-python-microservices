aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 360816483914.dkr.ecr.us-east-1.amazonaws.com
docker build -t morph .
docker tag morph:latest 360816483914.dkr.ecr.us-east-1.amazonaws.com/morph:latest
docker push 360816483914.dkr.ecr.us-east-1.amazonaws.com/morph:latest