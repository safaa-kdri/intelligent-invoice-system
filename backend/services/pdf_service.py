import os


def pdf_to_image(pdf_path: str, output_path: str, dpi: int = 200) -> str:
    """Convertit la première page d'un PDF en image PNG."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF introuvable : {pdf_path}")

    try:
        import pymupdf
    except ImportError:
        raise RuntimeError(
            "PyMuPDF n'est pas installé. Installez les dépendances backend."
        )

    try:
        document = pymupdf.open(pdf_path)
        if document.page_count == 0:
            raise ValueError("Le PDF ne contient aucune page.")

        page = document.load_page(0)
        zoom = dpi / 72.0
        matrix = pymupdf.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        pixmap.save(output_path)
        document.close()
        return output_path
    except Exception as exc:
        raise ValueError(f"Impossible de convertir le PDF : {exc}") from exc
