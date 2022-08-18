FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel
EXPOSE 20009/tcp
RUN apt-get update --allow-insecure-repositories
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install flask opencv-python
RUN pip3 install cmake boto3 ipdb
WORKDIR /home/morph_service
COPY /face_morpher /home/morph_service/face_morpher
RUN cd face_morpher&&pip install -r requirements.txt
RUN cd face_morpher&&python setup.py install
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/facemorpher-5.2.dev0-py3.7.egg/data
COPY shape_predictor_68_face_landmarks.dat /opt/conda/lib/python3.7/site-packages/facemorpher-5.2.dev0-py3.7.egg/data
COPY s3_functions.py /home/morph_service
COPY morph_service.py /home/morph_service
ENV AWS_ACCESS_KEY_ID=AKIAVIASWTZFO7GHDZF4
ENV AWS_SECRET_ACCESS_KEY=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
ENTRYPOINT ["python","-u","morph_service.py"]
# ENTRYPOINT ["tail"]
# CMD ["-f","/dev/null"]
