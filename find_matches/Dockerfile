FROM python:3.9.7
RUN pip install psycopg2 flask
RUN pip install pandas
RUN pip install geopy boto3 ipdb
WORKDIR /home/find_matches_service
COPY find_matches_service.py /home/find_matches_service
COPY sql_consts.py /home/find_matches_service
COPY server_consts.py /home/find_matches_service/
COPY ./dummy_users_stats.pkl /home/find_matches_service/
COPY postgres_client.py /home/find_matches_service
#COPY ./.aws /home/find_matches_service/.aws
EXPOSE 20002/tcp

ENTRYPOINT ["python","-u","find_matches_service.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]