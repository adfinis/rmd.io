FROM python:3.6

WORKDIR /app

RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -P /usr/local/bin \
    && chmod +x /usr/local/bin/wait-for-it.sh

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . /app

EXPOSE 8000