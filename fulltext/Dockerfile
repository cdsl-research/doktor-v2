FROM python:3.9-slim-buster
WORKDIR /work
COPY main.py requirements.txt /work/
RUN apt-get update && \
    apt-get install tk -y && \
    pip install -U pip && \
    pip install -r requirements.txt
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]
# CMD ["python", "main.py"]