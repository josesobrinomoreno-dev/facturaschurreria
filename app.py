import os
import base64
import io
from datetime import datetime

import requests
from flask import Flask, render_template, request
from pypdf import PdfReader, PdfWriter

app = Flask(__name__)

DESTINATARIO = os.environ.get("DESTINATARIO", "facturaschurreriamoreno@gmail.com")
GAS_URL = os.environ.get("GAS_URL", "")


def limpiar_nombre(texto):
    texto = (texto or "Proveedor").strip()
    return "".join(c for c in texto if c.isalnum() or c in " -_áéíóúÁÉÍÓÚñÑ.").strip() or "Proveedor"


def enviar_por_apps_script(nombre_archivo, data, mimetype, empresa, indice=None):
    if not GAS_URL:
        raise RuntimeError("Falta configurar la variable GAS_URL en Render")

    fecha = datetime.now().strftime("%d-%m-%Y")
    empresa_limpia = limpiar_nombre(empresa)
    extra = f" - {indice:02d}" if indice else ""
    asunto = f"Factura {empresa_limpia} - {fecha}{extra}"

    payload = {
        "asunto": asunto,
        "nombreArchivo": nombre_archivo,
        "mimeType": mimetype,
        "base64": base64.b64encode(data).decode("utf-8"),
    }

    respuesta = requests.post(GAS_URL, json=payload, timeout=90)
    respuesta.raise_for_status()
    return asunto


def dividir_pdf_por_paginas(pdf_data, empresa):
    reader = PdfReader(io.BytesIO(pdf_data))
    enviados = []
    fecha = datetime.now().strftime("%d-%m-%Y")
    empresa_limpia = limpiar_nombre(empresa)

    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        salida = io.BytesIO()
        writer.write(salida)
        archivo = f"Factura {empresa_limpia} - {fecha} - {i:02d}.pdf"
        asunto = enviar_por_apps_script(
            archivo,
            salida.getvalue(),
            "application/pdf",
            empresa_limpia,
            indice=i,
        )
        enviados.append(asunto)

    return enviados


@app.route("/", methods=["GET", "POST"])
def index():
    mensaje = None
    error = None

    if request.method == "POST":
        try:
            empresa = request.form.get("empresa", "Proveedor")
            tipo_envio = request.form.get("tipo_envio", "individual")
            archivo = request.files.get("archivo")

            if not archivo or not archivo.filename:
                raise RuntimeError("Selecciona un archivo antes de enviar")

            data = archivo.read()
            filename = archivo.filename
            mimetype = archivo.mimetype or "application/octet-stream"

            es_pdf = filename.lower().endswith(".pdf") or mimetype == "application/pdf"

            if tipo_envio == "multipagina" and es_pdf:
                enviados = dividir_pdf_por_paginas(data, empresa)
                mensaje = f"Enviado correctamente: {len(enviados)} correo(s), uno por página."
            else:
                asunto = enviar_por_apps_script(filename, data, mimetype, empresa)
                mensaje = f"Enviado correctamente: {asunto}"

        except Exception as e:
            error = f"Error enviando: {e}"

    return render_template("index.html", mensaje=mensaje, error=error, destinatario=DESTINATARIO)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
