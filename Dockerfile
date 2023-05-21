FROM python:3.11.0
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
COPY ./templates /code/templates
COPY ./static /code/static
COPY ./main.py /code/main.py
CMD [ "uvicorn", "main:app", "--host","0.0.0.0", "--port", "80"]