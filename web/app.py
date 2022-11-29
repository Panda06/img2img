import base64
import io
import zipfile

import click
import requests
import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from urllib3 import encode_multipart_formdata

SERVICE_URL = "http://0.0.0.0:8080/predict"
IMAGES_COUNT = 5


def get_response(img, image_name, images_count):
    body, headers = encode_multipart_formdata({
        "images_count": images_count,
        "img": (image_name, img, "image/jpeg")
    })
    return requests.post(url=SERVICE_URL, data=body, headers={"content-type": headers})


def create_app():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory='templates')

    @app.get('/', response_class=HTMLResponse)
    def get_root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.post('/', response_class=HTMLResponse)
    async def post_root(request: Request, img: UploadFile = File(...)):
        request_object_content = await img.read()
        img = io.BytesIO(request_object_content)

        response = get_response(img.getvalue(), "img", IMAGES_COUNT)

        if response.status_code == 200:
            images = []
            zfile = zipfile.ZipFile(io.BytesIO(response.content))
            zfile.extractall('.')
            for filename in zfile.namelist():
                image = Image.open(filename)
                im = io.BytesIO()
                image.save(im, "jpeg")
                images.append(base64.b64encode(im.getvalue()).decode('utf-8'))
            return templates.TemplateResponse("images_loaded.html",
                                              {"request": request,
                                               "request_image": base64.b64encode(img.getvalue()).decode("utf-8"),
                                               "images": images})

    return app


@click.command()
@click.option('-h', '--host', default='0.0.0.0')
@click.option('-p', '--port', default=8081)
def main(host, port):
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    main()
