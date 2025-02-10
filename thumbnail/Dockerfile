FROM python:3.12-slim-buster
WORKDIR /work
COPY main.py requirements.txt /work/
RUN pip install -U pip && \
    pip install -r requirements.txt
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]
