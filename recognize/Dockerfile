FROM baseai:3
RUN mkdir -p /home/recognition_service
WORKDIR /home/recognition_service
COPY play.py /home/recognition_service
COPY phil.jpg /home/recognition_service
ENTRYPOINT ["python", "-u","play.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]