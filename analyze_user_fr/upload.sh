aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 360816483914.dkr.ecr.us-east-1.amazonaws.com
docker build -t analyze_user_fr .
docker tag analyze_user_fr:latest 360816483914.dkr.ecr.us-east-1.amazonaws.com/analyze_user_fr:latest
docker push 360816483914.dkr.ecr.us-east-1.amazonaws.com/analyze_user_fr:latest