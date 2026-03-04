FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl_hale_bopp/ ./etl_hale_bopp/
COPY config/ ./config/
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

EXPOSE 3001

CMD ["python", "-m", "etl_hale_bopp", "webhook"]
