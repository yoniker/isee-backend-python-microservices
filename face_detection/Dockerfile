FROM public.ecr.aws/w0r4s6r3/baseai
RUN mkdir -p /home/face_detection_service
WORKDIR /home/face_detection_service
COPY image_utils.py /home/face_detection_service
COPY face_detection_service.py /home/face_detection_service
EXPOSE 20001/tcp
RUN pip install boto3
ENTRYPOINT ["python", "-u","face_detection_service.py"]