FROM python:3.8.0-alpine3.10 AS build

WORKDIR /tmp
RUN python -m pip install -U pip poetry
COPY pyproject.toml poetry.lock ./
COPY ./prepare_tool ./prepare_tool
RUN poetry build

FROM python:3.8.0-alpine3.10

WORKDIR /tmp
RUN echo http://dl-cdn.alpinelinux.org/alpine/edge/testing/ >> /etc/apk/repositories && \
  apk add --no-cache gcc libc-dev g++ bash git fontforge && \
  python -m pip install -U pip
COPY --from=build /tmp/dist/prepare_tool-0.0.1-py3-none-any.whl /tmp/prepare_tool-0.0.1-py3-none-any.whl
RUN pip install /tmp/prepare_tool-0.0.1-py3-none-any.whl
WORKDIR /workdir
LABEL io.whalebrew.name prepare_tool
ENTRYPOINT ["prepare_tool"]
