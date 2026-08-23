FROM python:3.14-slim
LABEL maintainer="Nemesis Noctis https://github.com/nemesis-noctis"
RUN apt-get update

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py migrate

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


