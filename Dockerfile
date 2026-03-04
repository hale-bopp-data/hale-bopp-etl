FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl_hale_bopp/ ./etl_hale_bopp/
COPY config/ ./config/

# Dagster home for run storage
RUN mkdir -p /opt/dagster
ENV DAGSTER_HOME=/opt/dagster

EXPOSE 3000

CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000", "-m", "etl_hale_bopp.definitions"]
