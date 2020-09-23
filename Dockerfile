FROM python:3.6

WORKDIR /app

RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -P /usr/local/bin \
    && chmod +x /usr/local/bin/wait-for-it.sh

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
ARG REQUIREMENTS=requirements.txt
COPY requirements.txt requirements-dev.txt /app/

RUN pip install -r $REQUIREMENTS --disable-pip-version-check

ADD . /app

EXPOSE 8000

CMD /bin/sh -c "wait-for-it.sh -t $WAIT_FOR_IT_TIMER $DATABASE_HOST:$DATABASE_PORT -- app/manage.py migrate && uwsgi"
