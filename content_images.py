import os
import secrets

from flask import current_app


MAX_CONTENT_IMAGE_BYTES = 3 * 1024 * 1024


def image_extension(data):
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return None


def save_content_image(upload, category):
    """Save a verified JPG or PNG with a generated filename; return None when no file was selected."""
    if upload is None or not getattr(upload, "filename", ""):
        return None

    data = upload.read(MAX_CONTENT_IMAGE_BYTES + 1)
    if len(data) > MAX_CONTENT_IMAGE_BYTES:
        raise ValueError("Please choose an image smaller than 3 MB.")

    extension = image_extension(data)
    if extension is None:
        raise ValueError("The selected file is not a valid JPG or PNG image.")

    folder = os.path.join(current_app.static_folder, "uploads", category)
    os.makedirs(folder, exist_ok=True)
    filename = f"{secrets.token_hex(16)}.{extension}"
    with open(os.path.join(folder, filename), "wb") as saved_file:
        saved_file.write(data)
    return filename


def delete_content_image(category, filename):
    if filename:
        folder = os.path.join(current_app.static_folder, "uploads", category)
        path = os.path.join(folder, os.path.basename(filename))
        if os.path.isfile(path):
            os.remove(path)
