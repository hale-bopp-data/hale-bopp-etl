FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hale_bopp_etl/ ./hale_bopp_etl/
COPY config/ ./config/
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

EXPOSE 3001

CMD ["python", "-m", "hale_bopp_etl", "webhook"]
