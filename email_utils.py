from email.mime.text import MIMEText
import smtplib
import pymysql


def get_credenciales_correo(id_correo=2):
    try:
        conn = pymysql.connect(
            host="192.168.1.14",
            user="root",
            password="Sw28Cw37",
            database="bdSupraliveRRHH"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT Correo, Contrasena FROM CORREOS_TBL WHERE IDcorreo = %s", (id_correo,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return resultado[0], resultado[1]  # (Correo, Contrasena)
        else:
            raise Exception("No se encontró el correo con IDcorreo = {}".format(id_correo))
    except Exception as e:
        print(f"Error al obtener credenciales del correo: {e}")
        raise

def send_email(begin_str, end_str, secuencial, cardname, recipient):
    """
    Envía un correo electrónico con la información de la guía.
    :param begin_str: Parte inicial del número (BeginStr)
    :param end_str: Parte intermedia del número (EndStr)
    :param secuencial: Parte final del número (Secuencial)
    :param cardname: Nombre del cliente
    :param recipient: Dirección de correo electrónico del cliente
    :return: True si el correo se envía con éxito, False en caso contrario
    """
    # Construcción del número concatenado
    numero_concatenado = f"{begin_str}-{end_str}-{secuencial}"

    # Construcción del contenido del correo
    message = f"""
    Estimado/a {cardname},

    Le informamos que se ha anulado la guía con número: {numero_concatenado}.

    Por favor, no dude en contactarnos si tiene alguna duda o requiere información adicional.

    Saludos cordiales,
    
    """
    try:
        # Obtener credenciales desde la base de datos
        correo_origen, contrasena = get_credenciales_correo(2)
        
        # Configuración del correo
        msg = MIMEText(message)
        msg["Subject"] = f"Anulación de Guía {numero_concatenado}"
        msg["From"] = "documentos.electronicos@supralive.com.ec"
        msg["To"] = recipient

        # Envío del correo
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.login(correo_origen, contrasena)
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        server.quit()
        print(f"Correo enviado correctamente a {recipient}.")
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
