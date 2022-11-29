import io
import logging
import os
import sys
import zipfile

TMP_DIR = "tmp"


def init_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)s]- %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def is_correct_image(image):
    extrema = image.convert("L").getextrema()
    return extrema != (0, 0)


def zipfiles(filenames):
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as temp_zip:
        for fpath in filenames:
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(TMP_DIR, fname)
            temp_zip.write(fpath, zip_path)
    return zip_io


def clear_tmp_files(filenames):
    for filename in filenames:
        os.remove(filename)
