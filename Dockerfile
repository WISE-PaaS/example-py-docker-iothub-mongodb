FROM python:3.6-slim  
WORKDIR /app  
ADD . /app  
RUN pip3 install -r requirements.txt

#Use in local
# EXPOSE 3000
# CMD ["python", "hello.py"]  