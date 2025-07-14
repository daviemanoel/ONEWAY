FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate
RUN python criar_dados_exemplo.py

EXPOSE 8000
CMD ["gunicorn", "oneway_admin.wsgi:application", "--bind", "0.0.0.0:8000"]