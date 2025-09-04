import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from database import login_user, fetch_sap_data, get_enviados, save_guia_cancelada
from email_utils import send_email
import threading
import schedule
import time


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Guías Canceladas")
        self.root.geometry("1000x700")

        # Spinner de carga
        self.loading_label = None

        # Inicia el background task
        self.start_background_task()

        self.create_login_screen()

    def start_background_task(self):
        """Inicia una tarea en segundo plano que actualiza los datos y envía correos automáticamente cada 15 minutos."""
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(1)

        # Programar la tarea de actualización de datos cada 15 minutos
        schedule.every(14).minutes.do(self.auto_update_data)

        # Programar la tarea de envío de correos cada 15 minutos
        schedule.every(15).minutes.do(self.auto_enviar_correos)

        # Crear un hilo para ejecutar el schedule
        threading.Thread(target=run_schedule, daemon=True).start()

    def auto_enviar_correos(self):
        """Envía automáticamente los correos electrónicos de las filas pendientes cada 15 minutos."""
        try:
            for item in self.tree.get_children():
                guia = self.tree.item(item)["values"]
                docnum, cardname, email, taxdate, numero_completo, estado = guia

                if estado == "Pendiente":
                    # Validar formato del número completo
                    if not isinstance(numero_completo, str) or "-" not in numero_completo or len(numero_completo.split('-')) != 3:
                        print(f"Formato inválido para número completo: {numero_completo}")
                        continue

                    begin_str, end_str, secuencial = numero_completo.split('-')

                    # Validar el correo
                    if not isinstance(email, str) or "@" not in email:
                        print(f"Correo inválido para {cardname}: {email}")
                        continue

                    # Enviar el correo
                    if send_email(begin_str, end_str, secuencial, cardname, email):
                        save_guia_cancelada(docnum, self.user_id, email)
                        self.tree.set(item, "Estado", "Enviado")

            print("Envío automático de correos completado.")
        except Exception as e:
            print(f"Error en el envío automático de correos: {e}")




    def auto_update_data(self):
        """Actualiza automáticamente los datos de la tabla si está en el dashboard."""
        print("Actualizando datos automáticamente...")
        if hasattr(self, "start_date_entry") and hasattr(self, "end_date_entry"):
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            self.show_loading_spinner("Actualizando datos...")
            self.fetch_guias_data(start_date, end_date)
            self.hide_loading_spinner()

    def show_loading_spinner(self, message="Cargando..."):
        """Muestra un spinner de carga."""
        if not self.loading_label:
            self.loading_label = tk.Label(self.root, text=message, font=("Poppins", 12), fg="blue")
            self.loading_label.pack(pady=10)

    def hide_loading_spinner(self):
        """Oculta el spinner de carga."""
        if self.loading_label:
            self.loading_label.destroy()
            self.loading_label = None

    def create_login_screen(self):
        """Crea la pantalla de inicio de sesión."""
        self.clear_window()

        # Fondo y diseño
        bg_frame = tk.Frame(self.root, bg="#080710")
        bg_frame.pack(fill="both", expand=True)

        tk.Label(bg_frame, text="Iniciar Sesión", font=("Poppins", 24), fg="white", bg="#080710").pack(pady=20)

        tk.Label(bg_frame, text="Usuario:", font=("Poppins", 12), fg="white", bg="#080710").pack(pady=5)
        self.username_entry = tk.Entry(bg_frame, font=("Poppins", 12), width=30)
        self.username_entry.pack(pady=5)

        tk.Label(bg_frame, text="Contraseña:", font=("Poppins", 12), fg="white", bg="#080710").pack(pady=5)
        self.password_entry = tk.Entry(bg_frame, show="*", font=("Poppins", 12), width=30)
        self.password_entry.pack(pady=5)

        tk.Button(bg_frame, text="Ingresar", font=("Poppins", 14), command=self.login, bg="white", fg="#080710").pack(pady=20)

    def login(self):
        """Valida las credenciales de usuario."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        result = login_user(username, password)
        if result:  # Si el inicio de sesión es exitoso
            self.username = username
            self.user_id = result[0]  # Guardar el IDusuario
            self.create_dashboard()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    def create_dashboard(self):
        """Crea la pantalla del dashboard."""
        self.clear_window()

        # Encabezado de navegación
        navbar = tk.Frame(self.root, bg="black", height=50)
        navbar.pack(fill="x")
        tk.Label(navbar, text=f"SapSupra - Bienvenido {self.username}", font=("Poppins", 16), fg="white", bg="black").pack(side="left", padx=20)
        tk.Button(navbar, text="Cerrar Sesión", font=("Poppins", 12), command=self.create_login_screen, bg="gray", fg="white").pack(side="right", padx=10)

        # Filtros de búsqueda
        filters_frame = tk.Frame(self.root)
        filters_frame.pack(fill="x", pady=10)

        tk.Label(filters_frame, text="Fecha Inicio:", font=("Poppins", 12)).grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = DateEntry(filters_frame, width=15, background="darkblue", foreground="white", borderwidth=2, date_pattern="yyyy-mm-dd")
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(filters_frame, text="Fecha Fin:", font=("Poppins", 12)).grid(row=0, column=2, padx=5, pady=5)
        self.end_date_entry = DateEntry(filters_frame, width=15, background="darkblue", foreground="white", borderwidth=2, date_pattern="yyyy-mm-dd")
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(filters_frame, text="Buscar", command=self.trigger_fetch_guias_data, font=("Poppins", 12), bg="blue", fg="white").grid(row=0, column=4, padx=10)

        # Tabla para mostrar los datos
        self.tree = ttk.Treeview(
            self.root,
            columns=("Numero Doc", "Cliente", "Correo", "Fecha Documento","Guia Remision" , "Estado"),
            show="headings"
        )
        self.tree.pack(fill="both", expand=True, pady=10, padx=10)

        # Configurar encabezados y tamaños de las columnas
        for col, width in zip(self.tree["columns"], [100, 200, 250, 150, 100, 150]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")


        # Botones de acción
        action_frame = tk.Frame(self.root)
        action_frame.pack(fill="x", pady=10)

        tk.Button(action_frame, text="Seleccionar Todos", command=self.select_all, font=("Poppins", 12), bg="blue", fg="white").pack(side="left", padx=10)
        tk.Button(action_frame, text="Deseleccionar Todo", command=self.deselect_all, font=("Poppins", 12), bg="gray", fg="white").pack(side="left", padx=10)
        tk.Button(action_frame, text="Enviar Correos", command=self.enviar_correos, font=("Poppins", 12), bg="green", fg="white").pack(side="right", padx=10)

    def trigger_fetch_guias_data(self):
        """Inicia el proceso de búsqueda con un spinner."""
        self.show_loading_spinner("Buscando datos...")
        self.root.after(100, self.fetch_guias_data)  # Agregar un pequeño delay para mostrar el spinner

    def fetch_guias_data(self, start_date=None, end_date=None):
        """Obtiene las guías desde SAP HANA y las muestra en la tabla."""
        start_date = start_date or self.start_date_entry.get()
        end_date = end_date or self.end_date_entry.get()

        try:
            sap_data = fetch_sap_data(start_date, end_date)
            enviados = get_enviados()

            # Limpiar los datos existentes en la tabla
            self.tree.delete(*self.tree.get_children())
            

            # Procesar los datos obtenidos de SAP
            for row in sap_data:
                # Generar el número completo
                numero_completo = f"{row[4]}-{row[5]}-{row[6]}"  # BeginStr, EndStr, Secuencial
                estado = "Enviado" if row[0] in enviados else "Pendiente"

                # Insertar los datos en el TreeView con los correos fijos y el número completo
                self.tree.insert(
                    "",
                    "end",
                    values=(row[0], row[1], row[2], row[3].strftime("%Y-%m-%d"), numero_completo, estado)
                )
        except Exception as e:
            messagebox.showerror("Error", f"Error conectando a SAP HANA: {e}")
        finally:
            self.hide_loading_spinner()

    def select_all(self):
        """Selecciona todas las filas de la tabla."""
        for item in self.tree.get_children():
            self.tree.selection_add(item)

    def deselect_all(self):
        """Deselecciona todas las filas en la tabla."""
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def enviar_correos(self):
        """Envía correos electrónicos seleccionados."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Por favor, selecciona al menos una guía para enviar.")
            return

        enviados_exitosos = []
        ya_enviados = []

        for item in selected_items:
            guia = self.tree.item(item)["values"]
            docnum, cardname, email, taxdate, numero_completo, estado = guia  # Ajustado el orden de extracción
            
            if estado == "Enviado":
                ya_enviados.append(docnum)
            else:
                # Verificar el formato de `numero_completo`
                if "-" not in numero_completo or len(numero_completo.split('-')) != 3:
                    print(f"Formato inválido para número completo: {numero_completo}")
                    messagebox.showerror("Error", f"Formato inválido para número completo: {numero_completo}")
                    continue

                # Desglosar el número completo
                begin_str, end_str, secuencial = numero_completo.split('-')

                # Intentar enviar el correo
                if send_email(begin_str, end_str, secuencial, cardname, email):
                    save_guia_cancelada(docnum, self.user_id, email)
                    enviados_exitosos.append(docnum)
                    self.tree.set(item, "Estado", "Enviado")

        # Construir mensaje de resultados
        mensaje = "Resultados del envío:\n"
        if enviados_exitosos:
            mensaje += f"Enviados exitosamente: {', '.join(map(str, enviados_exitosos))}\n"
        if ya_enviados:
            mensaje += f"Ya enviados anteriormente: {', '.join(map(str, ya_enviados))}\n"

        messagebox.showinfo("Resultados del Envío", mensaje)



    def clear_window(self):
        """Limpia todos los widgets de la ventana."""
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
