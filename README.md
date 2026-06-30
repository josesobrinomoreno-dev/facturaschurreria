# Facturas Churrería - versión simple

App Flask simple para subir una imagen/PDF y enviarla a Gmail/Odoo usando Google Apps Script.

## Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn --timeout 120 app:app
```

Variables necesarias:

```text
GAS_URL=https://script.google.com/macros/s/XXXX/exec
DESTINATARIO=facturaschurreriamoreno@gmail.com
```

## Google Apps Script

Crear un proyecto en https://script.google.com y pegar:

```javascript
function doPost(e) {
  const data = JSON.parse(e.postData.contents);

  const destinatario = "facturaschurreriamoreno@gmail.com";
  const asunto = data.asunto;
  const nombreArchivo = data.nombreArchivo;
  const mimeType = data.mimeType;
  const base64 = data.base64;

  const blob = Utilities.newBlob(
    Utilities.base64Decode(base64),
    mimeType,
    nombreArchivo
  );

  GmailApp.sendEmail(destinatario, asunto, "Factura adjunta", {
    attachments: [blob]
  });

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
```

Implementar como Aplicación web:
- Ejecutar como: Tú
- Quién tiene acceso: Cualquiera
