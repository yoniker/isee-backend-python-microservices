FROM python:3.9.7
RUN pip install sanic
WORKDIR /home/websockets_service
COPY websockets_service.py /home/websockets_service
EXPOSE 5000/tcp

ENTRYPOINT ["python","-u","websockets_service.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]