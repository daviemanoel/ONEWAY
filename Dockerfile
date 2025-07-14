FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set work directory
WORKDIR /app

# Copy Django project
COPY django_admin/ ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Collect static files, migrate, and create example data
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate
RUN python criar_dados_exemplo.py

# Expose port
EXPOSE $PORT

# Run gunicorn
CMD gunicorn oneway_admin.wsgi:application --bind 0.0.0.0:$PORT