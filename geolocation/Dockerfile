FROM python:3.9.7
RUN pip install psycopg2 flask
RUN pip install geopy
WORKDIR /home/geolocation_service
COPY geolocation_service.py /home/geolocation_service
COPY sql_consts.py /home/geolocation_service
COPY postgres_client.py /home/geolocation_service
#COPY ./.aws /home/find_matches_service/.aws
EXPOSE 20004/tcp

ENTRYPOINT ["python","-u","geolocation_service.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]