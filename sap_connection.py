from hdbcli import dbapi

def conectar_sap():
    try:
        connection = dbapi.connect(
            address='10.1.0.70',
            port=30015,
            user='SUPRALIVE',
            password='uGDH6%Yr$K'
        )
        return connection
    except dbapi.Error as e:
        print(f"Error al conectar con SAP HANA :{e} ")
    return None