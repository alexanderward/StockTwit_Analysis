# use base python image with python 2.7
FROM alpine:3.2

RUN apk add --update \
    python-dev \
    build-base \
    python \
    py-pip \
    postgresql-dev \
    gcc \
    && rm -rf /var/cache/apk/*
RUN pip install --upgrade pip
# add requirements.txt to the image
ADD src /app
ADD requirements.txt /app/requirements.txt
#ADD run.sh /app/run.sh

#RUN chmod +x /app/run.sh


# set working directory to /app/
WORKDIR /app/

# install python dependencies
RUN pip install -r requirements.txt