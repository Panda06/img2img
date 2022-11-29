FROM python:3.8-slim

COPY service/ /service
COPY service/configs/ /usr/local/lib/python3.8/site-packages/configs
WORKDIR /service/src

RUN pip install -U pip

RUN pip install ../blip-1.0-py3-none-any.whl

RUN pip install ../clip-1.0-py3-none-any.whl

RUN pip install -r ../requirements.txt

CMD ["python3", "app.py"]
