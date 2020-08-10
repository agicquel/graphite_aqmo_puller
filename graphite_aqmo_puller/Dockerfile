FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY ./graphite_aqmo_puller.py ./graphite_aqmo_puller.py

RUN pip install --no-cache-dir -r requirements.txt

ENV CARBON_SERVER "localhost"
ENV CARBON_PICKLE_PORT 2004
ENV AUTH ""

CMD [ "python", "./graphite_aqmo_puller.py" ]