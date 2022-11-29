import io
import logging
import os
import uuid

import click
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from PIL import Image

from model_singlton import Model
from tools import clear_tmp_files, init_logging, is_correct_image, TMP_DIR, zipfiles


def create_app():
    app = FastAPI(
        title="Similar images generator",
        version="0.1"
    )

    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)

    def prompt_to_images(prompt, images_count):
        result = []
        while len(result) < images_count:
            new_img = Model().get_image(prompt)
            filename = f"{uuid.uuid4()}.jpg"
            path = os.path.join(TMP_DIR, filename)
            new_img.save(path)
            result.append(path)
        return result

    def image2prompt(img):
        logging.info("Start get input image caption")
        prompt = Model().get_prompt(img)
        logging.info(f"Image caption: {prompt}")
        return prompt

    @app.on_event("startup")
    async def load_model():
        init_logging()
        logging.info("Start load models")
        Model()

    @app.get("/health")
    async def health() -> bool:
        logging.info("Health check")
        if Model.model is None:
            logging.error("Models didn't load")
            return False
        return True

    @app.post("/predict")
    async def predict(images_count: int = Form(...), img: UploadFile = File(...)):
        logging.info("Start predicting")
        logging.info("Getting input image")
        request_object_content = await img.read()
        img = Image.open(io.BytesIO(request_object_content)).convert("RGB")
        prompt = image2prompt(img)
        result = prompt_to_images(prompt, images_count)

        if len(result) > 0:
            z = zipfiles(result)
            return StreamingResponse(
                iter([z.getvalue()]),
                media_type="application/x-zip-compressed",
                headers={"Content-Disposition": f"attachment; filename=images.zip"},
                background=BackgroundTask(lambda: clear_tmp_files(result))
            )
        else:
            raise HTTPException(status_code=400, detail="Potential NSFW content was detected in input image")

    return app


@click.command()
@click.option('-h', '--host', default='0.0.0.0')
@click.option('-p', '--port', default=8080)
def main(host, port):
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
