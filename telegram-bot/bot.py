import os
import uuid
import zipfile
from io import BytesIO

import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from PIL import Image
from urllib3 import encode_multipart_formdata

from config import API_TOKEN

TMP_DIR = "tmp"
SERVICE_URL = "http://0.0.0.0:8080/predict"


async def get_response(img, image_name, images_count):
    body, headers = encode_multipart_formdata({
        "images_count": images_count,
        "img": (image_name, img, "image/jpeg")
    })
    return requests.post(url=SERVICE_URL, data=body, headers={"content-type": headers})


def create_dp():
    bot = Bot(API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    set_count = State()

    @dp.message_handler(commands=['start', 'help'])
    async def start(msg: types.Message):
        await msg.answer("I can generate similar images. Send me image")

    @dp.message_handler(commands=["set_count_images"])
    async def set_count_images(msg: types.Message):
        await msg.answer("How many images need to be generated")
        await set_count.set()

    @dp.message_handler(state=set_count)
    async def change_counts(msg: types.Message, state: FSMContext):
        try:
            count = int(msg.text)
            if count == 0:
                raise ValueError
        except ValueError:
            await msg.answer("Please send number and number greater than 0")
        else:
            async with state.proxy() as data:
                data["count"] = count
            await msg.answer(f"You will get {count} {'image' if count == 1 else 'images'}")

    @dp.message_handler(content_types=['photo'])
    async def process_image(msg: types.Message):
        print("Start processing query")
        data = await storage.get_data(user=msg.from_user.id)
        images_count = data.get('count', 5)
        img_name = f"{uuid.uuid4()}.jpg"
        dest_filename = os.path.join(TMP_DIR, img_name)
        await msg.photo[-1].download(destination_file=dest_filename)
        await msg.answer("Added your request to the queue. The result will be ready in about 2 minutes")
        with open(dest_filename, 'rb') as f:
            img = f.read()
            response = await get_response(img, img_name, images_count)
            if response.status_code == 200:
                zfile = zipfile.ZipFile(BytesIO(response.content))
                zfile.extractall('.')
                for filename in zfile.namelist():
                    image = Image.open(filename)
                    img_io = BytesIO()
                    img_io.name = filename
                    image.save(img_io, 'jpeg')
                    img_io.seek(0)
                    await msg.bot.send_photo(msg.from_user.id, img_io)
                    os.remove(filename)
            else:
                await msg.answer("Service is not available.")
        if os.path.exists(dest_filename):
            os.remove(dest_filename)

    @dp.message_handler()
    async def process_no_photo_msg(msg: types.Message):
        await msg.answer("Please send me image")

    return dp


if __name__ == '__main__':
    dp = create_dp()
    executor.start_polling(dp, skip_updates=False)
