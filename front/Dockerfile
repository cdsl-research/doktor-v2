# FROM python:3.9-alpine
FROM python:3.9-slim
WORKDIR /work
COPY main.py requirements.txt /work/
COPY templates/ /work/templates/
RUN apk add --update build-base libffi-dev && \
    pip install -U pip && \
    pip install -r requirements.txt
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]
