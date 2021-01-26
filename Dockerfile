FROM python:3.9-alpine


WORKDIR /usr/src/app

#COPY requirements.txt ./
#RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080/tcp

CMD [ "python", "./server.py", "--port=8080" ]
