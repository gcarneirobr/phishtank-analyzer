FROM python:3.6-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

COPY crontab.txt ./

RUN apk update && \
 apk add postgresql-libs && \
 apk add --virtual .build-deps gcc musl-dev postgresql-dev && \
 pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps && \ 
 /usr/bin/crontab crontab.txt

COPY . .

CMD ["./entry.sh"]