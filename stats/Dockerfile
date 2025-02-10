FROM python:3.12-alpine
WORKDIR /work
COPY main.py requirements.txt /work/
RUN apk add --update build-base libffi-dev python3-tkinter && \
    pip install -U pip && \
    pip install -r requirements.txt
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]
