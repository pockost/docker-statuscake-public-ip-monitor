FROM python:alpine3.7

LABEL Romain THERRAT="romain@pockost.com"

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

CMD python ./monitor_statuscake.py

