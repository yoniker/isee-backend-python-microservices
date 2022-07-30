FROM python:3.9.7
RUN pip install psycopg2 flask requests Pillow
RUN pip install pandas
RUN pip install geopy boto3 ipdb dnspython
RUN pip install firebase_admin
WORKDIR /home/user_data_service
COPY user_data_service.py /home/user_data_service
COPY sql_consts.py /home/user_data_service
COPY server_consts.py /home/user_data_service
COPY postgres_client.py /home/user_data_service
COPY image_utils.py /home/user_data_service/
COPY srv_resolve.py /home/user_data_service/
COPY swiper-db2c5-firebase-adminsdk-m30b7-66825f6744.json /home/user_data_service/
ENV GOOGLE_APPLICATION_CREDENTIALS /home/user_data_service/swiper-db2c5-firebase-adminsdk-m30b7-66825f6744.json
#ENV AWS_ACCESS_KEY_ID=AKIAVIASWTZFO7GHDZF4
#ENV AWS_SECRET_ACCESS_KEY=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
EXPOSE 20003/tcp

ENTRYPOINT ["python","-u","user_data_service.py"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]