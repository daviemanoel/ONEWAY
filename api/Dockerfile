FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py setup_database && python manage.py collectstatic --noinput && gunicorn oneway_admin.wsgi:application --bind 0.0.0.0:8000"]