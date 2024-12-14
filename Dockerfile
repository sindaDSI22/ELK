FROM python:3.9

WORKDIR /app

COPY requirements.txt requirements.txt
COPY app.py app.py
COPY templates/ templates/
COPY .env .env

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]