FROM python:3.7-alpine

WORKDIR /tmp

RUN apk add --no-cache gcc libc-dev g++ bash git && \
  python -m pip install -U pip pipenv

COPY Pipfile Pipfile.lock setup.py ./
COPY ./fonts_builder ./fonts_builder
RUN pipenv lock -r > requirements.txt && \
  pip install .

WORKDIR /workdir

CMD ["bash"]
