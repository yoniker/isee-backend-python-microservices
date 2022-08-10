FROM python:3.9.7
RUN pip install starlette uvicorn[standard]
WORKDIR /home/websockets_service
COPY run.py /home/websockets_service
COPY app.py /home/websockets_service
EXPOSE 5000/tcp

ENTRYPOINT ["python","-u","run.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]