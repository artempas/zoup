# syntax=docker/dockerfile:1
FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -yq tzdata && \
    dpkg-reconfigure -f noninteractive tzdata
WORKDIR /Grocery_bot
COPY . /Grocery_bot/
RUN pip install -r requirements.txt
ENV PYTHONPATH /Grocery_bot
