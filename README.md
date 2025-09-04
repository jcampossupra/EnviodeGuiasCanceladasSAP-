Se necesita este comando para crear el ejecutable con el icono y la libreria de mysql
pyinstaller --onefile --hidden-import pymysql --icon=email_102148.ico --noconsole main.py
