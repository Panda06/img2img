FROM python:3.8-slim

COPY web/ /web

WORKDIR /web

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["app.py"]