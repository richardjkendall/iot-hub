FROM python:3.8-alpine

ADD requirements.txt .
ADD *.py .
RUN pip install -r requirements.txt

# volumes
VOLUME "/data"  
VOLUME "/bin"  

CMD [ "gunicorn", "--timeout", "600", "--bind", "0.0.0.0:8000", "-w", "4", "app:app" ]