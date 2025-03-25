import qrcode
import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuración de SMTP (para Gmail)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = os.environ.get('SMTP_PORT', 587)
GMAIL_USER = os.environ.get('EMAIL_USER')  # Tu correo de Gmail (en variable de entorno)
GMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')  # Tu contraseña de Gmail o contraseña de aplicación

# Función para enviar correo electrónico
def send_email(recipient_email, qr_image_path, pedido_id):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = f"Tu código QR para el pedido {pedido_id}"

        # Cuerpo del correo
        body = MIMEText(f"Hola,\n\nAquí tienes el código QR para tu pedido {pedido_id}. El código QR es válido hasta la expiración indicada.", 'plain')
        msg.attach(body)

        # Adjuntar la imagen del QR
        with open(qr_image_path, 'rb') as qr_file:
            qr_image = MIMEImage(qr_file.read())
            qr_image.add_header('Content-Disposition', 'attachment', filename=os.path.basename(qr_image_path))
            msg.attach(qr_image)

        # Enviar el correo
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Activar cifrado TLS
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, recipient_email, msg.as_string())

        print(f"Correo enviado a {recipient_email} con el código QR.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

@app.route('/')
def index():
    return "Servidor Flask en funcionamiento"

@app.route('/generar_qr', methods=['POST'])
def generar_qr():
    try:
        # Obtener los datos del cuerpo de la solicitud
        data = request.get_json()

        # Verificar que los datos necesarios estén presentes
        if 'pedido_id' not in data or 'expiracion' not in data:
            return jsonify({'error': 'Faltan parámetros en la solicitud'}), 400

        pedido_id = data['pedido_id']
        expiracion = data['expiracion']

        # Crear el contenido del QR
        qr_content = f"{pedido_id},{expiracion}"

        # Generar el código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        # Crear la imagen del QR
        img = qr.make_image(fill='black', back_color='white')

        # Crear un nombre único para el archivo QR
        qr_filename = f"{pedido_id}.png"

        # Guardar el archivo en la carpeta 'static'
        img_path = os.path.join('static', qr_filename)
        img.save(img_path)

        # Calcular la fecha de expiración en formato UNIX (timestamp)
        expiration_time = time.time() + expiracion

        # Enviar el código QR a tu correo personal (ya configurado)
        send_email(GMAIL_USER, img_path, pedido_id)  # Enviar a tu correo personal

        # Devolver la respuesta con el enlace al QR y la expiración
        return jsonify({
            'pedido_id': pedido_id,
            'expiracion': expiration_time,
            'qr_url': img_path
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
