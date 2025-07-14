FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate
RUN python criar_dados_exemplo.py

CMD ["sh", "-c", "python test_db.py && python manage.py migrate && gunicorn oneway_admin.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]