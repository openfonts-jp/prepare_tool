FROM python:3.7.4-alpine3.10

WORKDIR /tmp

RUN echo http://dl-cdn.alpinelinux.org/alpine/edge/testing/ >> /etc/apk/repositories && \
  apk add --no-cache gcc libc-dev g++ bash git fontforge && \
  python -m pip install -U pip pipenv

COPY Pipfile Pipfile.lock setup.py ./
COPY ./prepare_tool ./prepare_tool
RUN pipenv lock -r > requirements.txt && \
  pip install .

WORKDIR /workdir

LABEL io.whalebrew.name prepare_tool

ENTRYPOINT ["prepare_tool"]
