FROM python:3.9.7
RUN pip install psycopg2 flask requests Pillow
RUN pip install boto3 ipdb dnspython
RUN pip install pandas
WORKDIR /home/analyze_user_fr_service
COPY analyze_user_fr.py /home/analyze_user_fr_service
COPY sql_consts.py /home/analyze_user_fr_service
COPY postgres_client.py /home/analyze_user_fr_service
COPY image_utils.py /home/analyze_user_fr_service
COPY srv_resolve.py /home/analyze_user_fr_service/
COPY s3_functions.py /home/analyze_user_fr_service/
COPY group_faces.py /home/analyze_user_fr_service/
COPY celebs.pickle /home/analyze_user_fr_service/
COPY free_celebs_data.pickle /home/analyze_user_fr_service/
COPY faceDetectionsApi.py /home/analyze_user_fr_service/
# ENV AWS_ACCESS_KEY_ID=AKIAVIASWTZFO7GHDZF4
# ENV AWS_SECRET_ACCESS_KEY=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
EXPOSE 20006/tcp

ENTRYPOINT ["python","-u","analyze_user_fr.py"]
# ENTRYPOINT ["tail"]
# CMD ["-f","/dev/null"]