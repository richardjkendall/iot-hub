FROM python:3.8-alpine

ADD requirements.txt .
ADD *.py .
ADD start.sh .
RUN pip install -r requirements.txt

# volumes
VOLUME "/data"  
VOLUME "/bin"  

ENTRYPOINT [ "./start.sh" ]