FROM nginx:1.19.0-alpine

COPY ./default.conf /etc/nginx/conf.d/default.conf
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir /home/app
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static
WORKDIR $APP_HOME