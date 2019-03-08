FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /code
WORKDIR /code
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
ENV PATH="/root/.poetry/bin:${PATH}"
COPY . /code
RUN poetry install --extras mysql-python --extras pgsql