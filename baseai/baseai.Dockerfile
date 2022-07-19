FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel
RUN apt-get update --allow-insecure-repositories
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install flask opencv-python
COPY ./FaceRecognition/ /opt/conda/lib/python3.7/site-packages/FaceRecognition
COPY ./FaceDetection/ /opt/conda/lib/python3.7/site-packages/FaceDetection
#EXPOSE 20000/tcp
#ENTRYPOINT ["python", "send_email_service.py"]
ENTRYPOINT ["tail"]
CMD ["-f","/dev/null"]