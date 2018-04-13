FROM python:3.5.1
MAINTAINER  Vulcanhy<vulcanhy@gmail.com>
            Responsible <responsible01@yeah.net>

RUN echo "Asia/Shanghai" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN pip install -r requirements.txt

RUN apt-get update -y
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:fkrull/deadsnakes
RUN apt-get install -y python2.7
RUN wget https://bootstrap.pypa.io/ez_setup.py -O - | python2.7
RUN easy_install-2.7 pip
RUN pip2.7 install supervisor

EXPOSE 5000

#CMD supervisord -c ./supervisor.ini

CMD gunicorn --bind 0.0.0.0:5000 -k gevent --workers 4 manage:app