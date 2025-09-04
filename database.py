import pymysql
from sap_connection import conectar_sap
from datetime import datetime
import hashlib

def get_connection():
    """Establece la conexión con la base de datos MySQL utilizando PyMySQL."""
    try:
        conn = pymysql.connect(
            host="192.168.1.14",
            user="root",
            password="Sw28Cw37",
            database="bdSupraliveRRHH"
        )
        print("Conexión exitosa a la base de datos")
        return conn
    except pymysql.MySQLError as err:
        print(f"Error al conectar a la base de datos: {err}")
        raise

def login_user(username, password):
    """Valida el usuario y contraseña utilizando la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    md5_password = hashlib.md5(password.encode()).hexdigest()
    try:
        cursor.execute(
            "SELECT IDusuario FROM USUARIO_TBL WHERE usuario = %s AND contrasena = %s",
            (username, md5_password)
        )
        result = cursor.fetchone()
        return result  # Devuelve el IDusuario si las credenciales son correctas, o None
    finally:
        conn.close()

def fetch_sap_data(start_date, end_date):
    """Obtiene datos de SAP HANA según las fechas."""
    try:
        connection_sap = conectar_sap()
        if connection_sap:
            cursor = connection_sap.cursor()
            query = f"""
            SELECT T0."DocNum", T0."CardName", T2."E_Mail", T0."TaxDate",T5."BeginStr",T5."EndStr"
            ,'00' || SUBSTRING(cast(T4."U_HBT_CodEnumeracion" as varchar),3,LENGTH(T4."U_HBT_CodEnumeracion") - 2) AS "secuencial"
            FROM SBO_EC_TENA12_02.ODLN T0
            LEFT JOIN SBO_EC_TENA12_02.RDN1 T1 ON T0."DocEntry" = T1."BaseEntry"
            INNER JOIN SBO_EC_TENA12_02.OCRD T2 ON T0."CardCode" = T2."CardCode"
            INNER JOIN SBO_EC_TENA12_02."@HBT_GUIAREMDETALLE" T3 ON T0."DocEntry" = T3."U_HBT_DocEntry"
            INNER JOIN SBO_EC_TENA12_02."@HBT_GUIAREMISION" T4 ON T4."Code" = T3."U_HBT_IdGuiaRemision"
            INNER JOIN SBO_EC_TENA12_02.NNM1 T5 ON T4."U_HBT_No" = T5."SeriesName" AND T5."ObjectCode" = 'GuiaRemision'
            WHERE T1."BaseType" = '15' AND T0."TaxDate" BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY T0."DocNum", T2."E_Mail", T0."CardName", T0."TaxDate",T4."U_HBT_CodEnumeracion",T5."BeginStr",T5."EndStr"
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            connection_sap.close()
            return rows
    except Exception as e:
        print(f"Error al conectar con SAP HANA: {e}")
        return []

def get_enviados():
    """Obtiene los documentos enviados desde la tabla GUIASREMISION_TBL."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT IDnumDoc FROM GUIASREMISION_TBL")
        enviados = {row[0] for row in cursor.fetchall()}
        return enviados
    finally:
        conn.close()

def save_guia_cancelada(docnum, idusuario, destinatario):
    """Guarda información de una guía cancelada."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO GUIASREMISION_TBL (IDnumDoc, IDusuario, FechaEnvio, Destinatario, Estado, RazonSocial)
        VALUES (%s, %s, NOW(), %s, %s, %s)
        """
        cursor.execute(query, (docnum, idusuario, destinatario, "1", None))
        conn.commit()
    finally:
        conn.close()
