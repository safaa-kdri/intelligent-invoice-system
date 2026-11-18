import os
import tempfile

import pymupdf

from services.pdf_service import pdf_to_image


def test_pdf_to_image():
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    png_fd, png_path = tempfile.mkstemp(suffix=".png")
    os.close(png_fd)

    try:
        document = pymupdf.open()
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 72), "Facture test")
        document.save(pdf_path)
        document.close()

        result = pdf_to_image(pdf_path, png_path)

        assert result == png_path
        assert os.path.exists(png_path)
        assert os.path.getsize(png_path) > 0
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(png_path):
            os.remove(png_path)
