FROM apache/airflow:slim-2.5.0-python3.9

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  graphviz libgraphviz-dev \
  libpq-dev \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow

COPY ./requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt
