FROM python:3.9.7
RUN pip install flask firebase_admin requests dnspython
WORKDIR /home/messaging_service
COPY messaging_service.py /home/messaging_service
COPY srv_resolve.py /home/messaging_service
COPY isee-art-firebase-adminsdk-o01re-bfcbc49c5a.json /home/messaging_service
EXPOSE 5000/tcp
ENV GOOGLE_APPLICATION_CREDENTIALS=/home/messaging_service/isee-art-firebase-adminsdk-o01re-bfcbc49c5a.json
ENTRYPOINT ["python","-u","messaging_service.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]