FROM python:3.9.7
RUN pip install psycopg2 flask requests google-api-python-client oauth2client cryptography
RUN pip install boto3 ipdb dnspython
RUN pip install ipdb
RUN pip install gunicorn
WORKDIR /home/premium_service
COPY premium_service.py /home/premium_service
COPY sql_consts.py /home/premium_service
COPY postgres_client.py /home/premium_service
COPY isee.json /home/premium_service
COPY crypt.py /home/premium_service
COPY iSee_symmetric_key.key /home/premium_service
COPY /keys/ /home/premium_service/keys
# ENV AWS_ACCESS_KEY_ID=AKIAVIASWTZFO7GHDZF4
# ENV AWS_SECRET_ACCESS_KEY=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
EXPOSE 20010/tcp
ENTRYPOINT ["python","-u","premium_service.py"]
#ENTRYPOINT ["gunicorn","-w","1","-b","0.0.0.0:20010","--certfile=keys/selfsigned.crt","--keyfile=keys/selfsigned.key","premium_service:app"]
#ENTRYPOINT ["gunicorn","-w","1","-b","0.0.0.0:20010","--certfile=keys/dordating.crt","--keyfile=keys/dordating.key","premium_service:app"]
#gunicorn -w 1 -b 0.0.0.0:20001 --certfile=keys/dordating.crt --keyfile=keys/dordating.key premium_service:app

# ENTRYPOINT ["tail"]
# CMD ["-f","/dev/null"]