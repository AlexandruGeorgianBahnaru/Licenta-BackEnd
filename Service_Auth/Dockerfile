
FROM python:3.10-slim

WORKDIR /app


COPY . .


RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (optional)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Specify the default command to run the application
CMD uvicorn main:app --port 80
