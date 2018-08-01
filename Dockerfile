FROM python:3.7-alpine

WORKDIR /tmp

RUN apk add --no-cache gcc libc-dev g++ bash git && \
  python -m pip install -U pip pipenv

COPY Pipfile Pipfile.lock setup.py ./
COPY ./prepare_tool ./prepare_tool
RUN pipenv lock -r > requirements.txt && \
  pip install .

WORKDIR /workdir

CMD ["bash"]
