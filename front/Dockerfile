FROM python:3.9-alpine
WORKDIR /work
COPY main.py requirements.txt /work/
COPY templates/ /work/templates/
COPY assets/ /work/assets/
RUN apk add --update build-base libffi-dev && \
    pip install -U pip && \
    pip install -r requirements.txt
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]
