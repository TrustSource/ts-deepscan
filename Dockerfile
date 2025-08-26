FROM python:3.12-slim
LABEL maintainer="Grigory Markin <gmn@eacg.de>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
       bzip2 \
       xz-utils \
       zlib1g \
       libxml2-dev \
       libxslt1-dev \
       libgomp1 \
       libsqlite3-0 \
       libgcrypt20 \
       libpopt0 \
       libzstd1 \
       libicu-dev \
       pkg-config \
       g++ \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /tmp/ts-deepscan
WORKDIR /tmp/ts-deepscan

COPY ./src ./src
COPY ./pyproject.toml ./LICENSE ./

RUN pip install ./

RUN rm -rf /tmp/ts-deepscan

ENTRYPOINT ["ts-deepscan"]
CMD []