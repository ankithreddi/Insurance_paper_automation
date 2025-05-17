FROM python:3.11

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt

# Expose VNC port
EXPOSE 8000


#Command to run
CMD ["python", "run.py"]
