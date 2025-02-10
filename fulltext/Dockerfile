FROM python:3.12-slim-bookworm
WORKDIR /work
COPY main.py requirements.txt /work/
RUN apt-get update && \
    apt-get install tk -y && \
    pip install -U pip && \
    pip install -r requirements.txt
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]
# CMD ["python", "main.py"]
