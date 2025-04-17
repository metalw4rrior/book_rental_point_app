FROM python:3.10-slim

WORKDIR /app

COPY biblioteka/ /app
COPY libratrack.dump /app
RUN apt-get update && apt-get install -y libpq-dev
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y postgresql-client

EXPOSE 5000

CMD ["python3", "main.py"]
