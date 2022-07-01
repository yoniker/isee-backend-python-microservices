FROM python:3.9.7
RUN pip install psycopg2 flask
WORKDIR /home/find_matches_service
COPY find_matches_service.py /home/find_matches_service
EXPOSE 20002/tcp

ENTRYPOINT ["python", "-u","find_matches_service.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]