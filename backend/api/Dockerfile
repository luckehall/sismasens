FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice in /srv/api/ così i relative import funzionano
# e uvicorn può importare il package come "api.main"
COPY . ./api

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
