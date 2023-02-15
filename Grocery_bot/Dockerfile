# syntax=docker/dockerfile:1
FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -yq tzdata && \
    dpkg-reconfigure -f noninteractive tzdata
WORKDIR /Bot
COPY ./requirements.txt /Bot/
RUN pip install -r requirements.txt
COPY . /Bot/
