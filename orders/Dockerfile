FROM python:3.9

WORKDIR /orders

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r /orders/requirements.txt

COPY . .
