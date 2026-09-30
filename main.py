"""
Gestor de Integrantes del Cabildo
----------------------------------
Aplicación de escritorio para registrar integrantes y sus documentos.
Guarda todo localmente: una base de datos SQLite + una carpeta de documentos,
ubicadas en la carpeta Documentos del usuario. Protegida con PIN de 4 dígitos.

Requiere: Python 3.9+ (Tkinter y sqlite3 vienen incluidos, no hay que instalar nada).
"""

import os
import sys
import re
import shutil
import sqlite3
import zipfile
import json
import hashlib
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "SistemaGestionInformacion"
DATA_DIR = os.path.join(os.path.expanduser("~"), "Documents", APP_NAME)
DOCS_DIR = os.path.join(DATA_DIR, "documentos")
DB_PATH = os.path.join(DATA_DIR, "cabildo.db")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
PIN_SALT = "cabildo-v1"  # protección básica, no es cifrado de nivel bancario

os.makedirs(DOCS_DIR, exist_ok=True)

COLOR_BG = "#f2f6f3"
COLOR_PANEL = "#ffffff"
COLOR_PRIMARY = "#2f6b4f"
COLOR_PRIMARY_DARK = "#1e4a37"
COLOR_DANGER = "#b0392f"
COLOR_DANGER_DARK = "#8a2c24"
COLOR_ACCENT = "#e6b25a"
COLOR_TEXT = "#1e2622"
COLOR_MUTED = "#6b7670"
FONT_BASE = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 10, "bold")
FECHA_PLACEHOLDER = "DD-MM-AAAA"


def resource_path(rel_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS integrantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cedula TEXT,
        comunidad TEXT,
        cargo TEXT,
        telefono TEXT,
        fecha_nacimiento TEXT,
        direccion TEXT,
        notas TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        integrante_id INTEGER NOT NULL,
        nombre_archivo TEXT NOT NULL,
        ruta_relativa TEXT NOT NULL,
        fecha_agregado TEXT,
        FOREIGN KEY(integrante_id) REFERENCES integrantes(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()


def abrir_archivo(ruta):
    try:
        if sys.platform.startswith("win"):
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.call(["open", ruta])
        else:
            subprocess.call(["xdg-open", ruta])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f)


def hash_pin(pin):
    return hashlib.sha256((pin + PIN_SALT).encode()).hexdigest()


def capitalizar_oraciones(texto):
    def cap(m):
        return m.group(1) + m.group(2).upper()
    texto = re.sub(r"(^\s*)([a-záéíóúñ])", cap, texto)
    texto = re.sub(r"([.!?]\s+)([a-záéíóúñ])", cap, texto)
    return texto


class PinDialog(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.title("Acceso protegido")
        self.geometry("340x300")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        try:
            self.iconbitmap(resource_path("assets/icon.ico"))
        except Exception:
            pass

        header = tk.Frame(self, bg=COLOR_PRIMARY, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="🔒 Acceso protegido", font=FONT_TITLE,
                 bg=COLOR_PRIMARY, fg="white").pack()

        body = tk.Frame(self, bg=COLOR_BG, padx=24, pady=18)
        body.pack(fill="both", expand=True)

        cfg = load_config()
        self.modo_crear = "pin_hash" not in cfg
        vcmd = (self.register(self._validar), "%P")

        if self.modo_crear:
            tk.Label(body, text="Primera vez: crea un PIN de 4 dígitos",
                     bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_LABEL, wraplength=280).pack(anchor="w")
            tk.Label(body, text="Nuevo PIN", bg=COLOR_BG, fg=COLOR_MUTED, font=FONT_LABEL).pack(anchor="w", pady=(14, 2))
            self.e1 = tk.Entry(body, show="●", font=("Segoe UI", 20), justify="center",
                                validate="key", validatecommand=vcmd)
            self.e1.pack(fill="x")
            tk.Label(body, text="Confirmar PIN", bg=COLOR_BG, fg=COLOR_MUTED, font=FONT_LABEL).pack(anchor="w", pady=(12, 2))
            self.e2 = tk.Entry(body, show="●", font=("Segoe UI", 20), justify="center",
                                validate="key", validatecommand=vcmd)
            self.e2.pack(fill="x")
            tk.Button(body, text="Crear PIN", command=self._crear, bg=COLOR_PRIMARY, fg="white",
                      activebackground=COLOR_PRIMARY_DARK, activeforeground="white",
                      font=FONT_BTN, relief="flat", pady=8, cursor="hand2").pack(fill="x", pady=(18, 0))
            self.e1.focus()
            self.e1.bind("<Return>", lambda e: self.e2.focus())
            self.e2.bind("<Return>", lambda e: self._crear())
        else:
            tk.Label(body, text="Ingresa tu PIN de 4 dígitos", bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_LABEL).pack(anchor="w")
            self.e1 = tk.Entry(body, show="●", font=("Segoe UI", 22), justify="center",
                                validate="key", validatecommand=vcmd)
            self.e1.pack(fill="x", pady=(10, 4))
            self.error_label = tk.Label(body, text="", fg=COLOR_DANGER, bg=COLOR_BG, font=FONT_LABEL)
            self.error_label.pack(anchor="w")
            tk.Button(body, text="Ingresar", command=self._verificar, bg=COLOR_PRIMARY, fg="white",
                      activebackground=COLOR_PRIMARY_DARK, activeforeground="white",
                      font=("Segoe UI", 13, "bold"), relief="flat", pady=12, cursor="hand2").pack(fill="x", pady=(18, 6))
            tk.Button(body, text="Cambiar PIN", command=self._abrir_cambiar_pin, bg="white", fg=COLOR_PRIMARY,
                      activebackground="#e9f2ec", font=("Segoe UI", 9, "bold"), relief="flat",
                      pady=6, cursor="hand2").pack(fill="x")
            self.e1.focus()
            self.e1.bind("<Return>", lambda e: self._verificar())

    def _abrir_cambiar_pin(self):
        ChangePinDialog(self)

    def _validar(self, valor):
        return (valor.isdigit() and len(valor) <= 4) or valor == ""

    def _crear(self):
        p1, p2 = self.e1.get(), self.e2.get()
        if len(p1) != 4:
            messagebox.showwarning("PIN inválido", "El PIN debe tener 4 dígitos.", parent=self)
            return
        if p1 != p2:
            messagebox.showwarning("No coincide", "Los dos PIN no coinciden.", parent=self)
            self.e2.delete(0, "end")
            return
        cfg = load_config()
        cfg["pin_hash"] = hash_pin(p1)
        save_config(cfg)
        self.destroy()
        self.on_success()

    def _verificar(self):
        cfg = load_config()
        if hash_pin(self.e1.get()) == cfg.get("pin_hash"):
            self.destroy()
            self.on_success()
        else:
            self.error_label.config(text="PIN incorrecto, intenta de nuevo.")
            self.e1.delete(0, "end")


class ChangePinDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Cambiar PIN")
        self.geometry("340x380")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.grab_set()

        try:
            self.iconbitmap(resource_path("assets/icon.ico"))
        except Exception:
            pass

        header = tk.Frame(self, bg=COLOR_PRIMARY, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="🔑 Cambiar PIN", font=FONT_TITLE, bg=COLOR_PRIMARY, fg="white").pack()

        body = tk.Frame(self, bg=COLOR_BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        vcmd = (self.register(lambda v: (v.isdigit() and len(v) <= 4) or v == ""), "%P")

        def campo(texto):
            tk.Label(body, text=texto, bg=COLOR_BG, fg=COLOR_MUTED, font=FONT_LABEL).pack(anchor="w")
            e = tk.Entry(body, show="●", font=("Segoe UI", 16), justify="center",
                         validate="key", validatecommand=vcmd)
            e.pack(fill="x", pady=(2, 10))
            return e

        self.e_actual = campo("PIN actual")
        self.e_nuevo = campo("Nuevo PIN")
        self.e_confirma = campo("Confirmar nuevo PIN")

        self.error_label = tk.Label(body, text="", fg=COLOR_DANGER, bg=COLOR_BG, font=FONT_LABEL, wraplength=280)
        self.error_label.pack(anchor="w")

        tk.Button(body, text="Guardar nuevo PIN", command=self._guardar, bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_DARK, activeforeground="white",
                  font=FONT_BTN, relief="flat", pady=10, cursor="hand2").pack(fill="x", pady=(10, 0))
        self.e_actual.focus()

    def _guardar(self):
        cfg = load_config()
        if hash_pin(self.e_actual.get()) != cfg.get("pin_hash"):
            self.error_label.config(text="El PIN actual no es correcto.")
            return
        nuevo, confirma = self.e_nuevo.get(), self.e_confirma.get()
        if len(nuevo) != 4:
            self.error_label.config(text="El nuevo PIN debe tener 4 dígitos.")
            return
        if nuevo != confirma:
            self.error_label.config(text="El nuevo PIN no coincide con la confirmación.")
            return
        cfg["pin_hash"] = hash_pin(nuevo)
        save_config(cfg)
        messagebox.showinfo("Listo", "El PIN fue actualizado. Ingresa con tu nuevo PIN.", parent=self)
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Información")
        self.geometry("1100x660")
        self.minsize(950, 580)
        self.configure(bg=COLOR_BG)
        self.current_id = None

        try:
            self.iconbitmap(resource_path("assets/icon.ico"))
        except Exception:
            pass

        self._set_style()
        self.withdraw()
        PinDialog(self, self._iniciar_app)

    def _iniciar_app(self):
        self.deiconify()
        self._build_menu()
        self._build_header()
        self._build_layout()
        self.refresh_list()

    def _set_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_BASE)
        style.configure("Muted.TLabel", background=COLOR_BG, foreground=COLOR_MUTED, font=FONT_LABEL)
        style.configure("TEntry", padding=6, fieldbackground="white")
        style.configure("Treeview", rowheight=28, font=FONT_BASE, background="white",
                         fieldbackground="white", foreground=COLOR_TEXT)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"),
                         background=COLOR_PRIMARY, foreground="white")
        style.map("Treeview", background=[("selected", COLOR_PRIMARY)], foreground=[("selected", "white")])
        style.configure("Primary.TButton", background=COLOR_PRIMARY, foreground="white",
                         font=FONT_BTN, padding=(14, 9), borderwidth=0)
        style.map("Primary.TButton", background=[("active", COLOR_PRIMARY_DARK)])
        style.configure("Secondary.TButton", background="white", foreground=COLOR_PRIMARY,
                         font=FONT_BTN, padding=(12, 8), borderwidth=1, relief="solid")
        style.map("Secondary.TButton", background=[("active", "#e9f2ec")])
        style.configure("Danger.TButton", background=COLOR_DANGER, foreground="white",
                         font=FONT_BTN, padding=(14, 9), borderwidth=0)
        style.map("Danger.TButton", background=[("active", COLOR_DANGER_DARK)])

    def _build_header(self):
        header = tk.Frame(self, bg=COLOR_PRIMARY)
        header.pack(fill="x")
        try:
            img = tk.PhotoImage(file=resource_path("assets/logo.png"))
            img = img.subsample(max(img.width() // 48, 1), max(img.height() // 48, 1))
            self._logo_ref = img
            tk.Label(header, image=img, bg=COLOR_PRIMARY).pack(side="left", padx=14, pady=10)
        except Exception:
            pass
        tk.Label(header, text="Sistema de Gestión de Información", font=FONT_TITLE,
                 bg=COLOR_PRIMARY, fg="white").pack(side="left", pady=10)
        tk.Button(header, text="+ Nuevo integrante", command=self.nuevo,
                  bg=COLOR_ACCENT, fg=COLOR_PRIMARY_DARK, activebackground="#d9a248",
                  font=FONT_BTN, relief="flat", padx=16, pady=8, cursor="hand2").pack(side="right", padx=16)

    def _build_menu(self):
        menubar = tk.Menu(self)
        archivo = tk.Menu(menubar, tearoff=0)
        archivo.add_command(label="Crear respaldo (.zip)", command=self.crear_respaldo)
        archivo.add_command(label="Restaurar respaldo (.zip)", command=self.restaurar_respaldo)
        archivo.add_separator()
        archivo.add_command(label="Exportar a Excel (.xlsx)", command=self.exportar_excel)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.destroy)
        menubar.add_cascade(label="Archivo", menu=archivo)
        self.config(menu=menubar)

    def _build_layout(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, style="Panel.TFrame", padding=12, width=380)
        left.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(left, text="Buscar (nombre, cédula o comunidad):", style="Muted.TLabel", background=COLOR_PANEL).pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_list())
        ttk.Entry(left, textvariable=self.search_var).pack(fill="x", pady=(2, 8))

        self.count_label = ttk.Label(left, text="", style="Muted.TLabel", background=COLOR_PANEL)
        self.count_label.pack(anchor="w")

        cols = ("nombre", "cedula", "comunidad")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=24)
        for col, w in zip(cols, (170, 90, 110)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True, pady=(4, 8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        ttk.Button(left, text="+ Nuevo integrante", style="Primary.TButton", command=self.nuevo).pack(fill="x")
        ttk.Button(left, text="Exportar a Excel", style="Secondary.TButton", command=self.exportar_excel).pack(fill="x", pady=(6, 0))

        right = ttk.Frame(main, style="Panel.TFrame", padding=16)
        right.pack(side="left", fill="both", expand=True)

        form = ttk.Frame(right, style="Panel.TFrame")
        form.pack(fill="x")

        self.fields = {}
        campos_texto = {"nombre", "comunidad", "cargo", "direccion"}
        labels = [
            ("nombre", "Nombre completo *"), ("cedula", "N° de documento *"),
            ("comunidad", "Comunidad / vereda"), ("cargo", "Cargo en el cabildo"),
            ("telefono", "Teléfono"), ("fecha_nacimiento", "Fecha de nacimiento (DD-MM-AAAA)"),
            ("direccion", "Dirección"),
        ]
        entry_order = []
        for i, (key, label) in enumerate(labels):
            r, c = divmod(i, 2)
            frame = ttk.Frame(form, style="Panel.TFrame")
            frame.grid(row=r, column=c, sticky="ew", padx=5, pady=5)
            ttk.Label(frame, text=label, style="Muted.TLabel", background=COLOR_PANEL).pack(anchor="w")
            if key == "fecha_nacimiento":
                entry = tk.Entry(frame, width=35, font=FONT_BASE, relief="solid", borderwidth=1,
                                  foreground=COLOR_MUTED)
                entry.insert(0, FECHA_PLACEHOLDER)
                entry.bind("<KeyRelease>", self._formatear_fecha)
                entry.bind("<FocusIn>", self._fecha_focus_in)
                entry.bind("<FocusOut>", self._fecha_focus_out)
            else:
                entry = ttk.Entry(frame, width=35, font=FONT_BASE)
            entry.pack(fill="x", ipady=3)
            self.fields[key] = entry
            entry_order.append((key, entry))
            if key in campos_texto:
                entry.bind("<KeyRelease>", self._auto_mayuscula_entry)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        for i, (key, entry) in enumerate(entry_order):
            destino = entry_order[i + 1][1] if i + 1 < len(entry_order) else None
            entry.bind("<Return>", self._make_enter_handler(destino))

        ttk.Label(right, text="Notas", style="Muted.TLabel", background=COLOR_PANEL).pack(anchor="w", pady=(10, 2))
        self.notas_text = tk.Text(right, height=3, font=FONT_BASE, relief="solid", borderwidth=1)
        self.notas_text.pack(fill="x")
        self.notas_text.bind("<KeyRelease>", self._auto_mayuscula_text)

        btns = ttk.Frame(right, style="Panel.TFrame")
        btns.pack(fill="x", pady=12)
        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=self.guardar).pack(side="left")
        ttk.Button(btns, text="Eliminar integrante", style="Danger.TButton", command=self.eliminar).pack(side="left", padx=8)

        ttk.Label(right, text="Documentos adjuntos", style="Muted.TLabel", background=COLOR_PANEL).pack(anchor="w", pady=(6, 2))
        doc_frame = ttk.Frame(right, style="Panel.TFrame")
        doc_frame.pack(fill="both", expand=True)

        self.doc_list = tk.Listbox(doc_frame, height=8, font=FONT_BASE, relief="solid", borderwidth=1,
                                    selectbackground=COLOR_PRIMARY)
        self.doc_list.pack(side="left", fill="both", expand=True)
        self.doc_list.bind("<Double-Button-1>", lambda e: self.abrir_doc())

        doc_btns = ttk.Frame(doc_frame, style="Panel.TFrame")
        doc_btns.pack(side="left", fill="y", padx=8)
        ttk.Button(doc_btns, text="Agregar...", style="Secondary.TButton", command=self.agregar_doc).pack(fill="x", pady=3)
        ttk.Button(doc_btns, text="Abrir", style="Secondary.TButton", command=self.abrir_doc).pack(fill="x", pady=3)
        ttk.Button(doc_btns, text="Quitar", style="Secondary.TButton", command=self.quitar_doc).pack(fill="x", pady=3)

    def _fecha_focus_in(self, event):
        widget = event.widget
        if widget.get() == FECHA_PLACEHOLDER:
            widget.delete(0, "end")
            widget.config(foreground=COLOR_TEXT)

    def _fecha_focus_out(self, event):
        widget = event.widget
        if not widget.get():
            widget.insert(0, FECHA_PLACEHOLDER)
            widget.config(foreground=COLOR_MUTED)

    def _formatear_fecha(self, event):
        widget = event.widget
        texto = widget.get()
        if texto == FECHA_PLACEHOLDER:
            return
        digitos = re.sub(r"\D", "", texto)[:8]
        partes = []
        if len(digitos) > 4:
            partes.append(digitos[:2])
            partes.append(digitos[2:4])
            partes.append(digitos[4:])
        elif len(digitos) > 2:
            partes.append(digitos[:2])
            partes.append(digitos[2:])
        elif digitos:
            partes.append(digitos)
        nuevo = "-".join(partes)
        if nuevo != texto:
            widget.delete(0, "end")
            widget.insert(0, nuevo)
            widget.icursor(len(nuevo))

    def _make_enter_handler(self, destino):
        def handler(event):
            if destino is not None:
                destino.focus_set()
            return "break"
        return handler

    def _auto_mayuscula_entry(self, event):
        widget = event.widget
        texto = widget.get()
        nuevo = capitalizar_oraciones(texto)
        if nuevo != texto:
            pos = widget.index(tk.INSERT)
            widget.delete(0, "end")
            widget.insert(0, nuevo)
            widget.icursor(pos)

    def _auto_mayuscula_text(self, event):
        widget = event.widget
        texto = widget.get("1.0", "end-1c")
        nuevo = capitalizar_oraciones(texto)
        if nuevo != texto:
            idx = widget.index(tk.INSERT)
            widget.delete("1.0", "end")
            widget.insert("1.0", nuevo)
            widget.mark_set(tk.INSERT, idx)

    def refresh_list(self):
        term = self.search_var.get().strip().lower()
        conn = get_conn()
        rows = conn.execute(
            "SELECT id, nombre, cedula, comunidad FROM integrantes ORDER BY nombre"
        ).fetchall()
        conn.close()

        filtered = [
            r for r in rows
            if not term or term in (r[1] or "").lower() or term in (r[2] or "").lower() or term in (r[3] or "").lower()
        ]
        self.count_label.config(text=f"{len(filtered)} de {len(rows)} integrantes")

        self.tree.delete(*self.tree.get_children())
        for r in filtered:
            self.tree.insert("", "end", iid=r[0], values=(r[1], r[2] or "-", r[3] or "-"))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        self.cargar_integrante(int(sel[0]))

    def limpiar_form(self):
        for entry in self.fields.values():
            entry.delete(0, "end")
        self.fields["fecha_nacimiento"].insert(0, FECHA_PLACEHOLDER)
        self.fields["fecha_nacimiento"].config(foreground=COLOR_MUTED)
        self.notas_text.delete("1.0", "end")
        self.doc_list.delete(0, "end")
        self.current_id = None

    def nuevo(self):
        self.limpiar_form()
        self.tree.selection_remove(self.tree.selection())
        self.fields["nombre"].focus()

    def cargar_integrante(self, id_):
        conn = get_conn()
        row = conn.execute(
            "SELECT nombre, cedula, comunidad, cargo, telefono, fecha_nacimiento, direccion, notas "
            "FROM integrantes WHERE id=?", (id_,)
        ).fetchone()
        conn.close()
        if not row:
            return

        self.current_id = id_
        keys = ["nombre", "cedula", "comunidad", "cargo", "telefono", "fecha_nacimiento", "direccion"]
        for key, val in zip(keys, row[:-1]):
            self.fields[key].delete(0, "end")
            if key == "fecha_nacimiento":
                if val:
                    self.fields[key].insert(0, val)
                    self.fields[key].config(foreground=COLOR_TEXT)
                else:
                    self.fields[key].insert(0, FECHA_PLACEHOLDER)
                    self.fields[key].config(foreground=COLOR_MUTED)
            else:
                self.fields[key].insert(0, val or "")
        self.notas_text.delete("1.0", "end")
        self.notas_text.insert("1.0", row[-1] or "")

        self.refresh_docs()

    def guardar(self):
        nombre = self.fields["nombre"].get().strip()
        cedula = self.fields["cedula"].get().strip()
        if not nombre or not cedula:
            messagebox.showwarning("Falta información", "Nombre y número de documento son obligatorios.")
            return

        fecha_raw = self.fields["fecha_nacimiento"].get().strip()
        fecha = "" if fecha_raw == FECHA_PLACEHOLDER else fecha_raw
        if fecha:
            if not re.match(r"^\d{2}-\d{2}-\d{4}$", fecha):
                messagebox.showwarning("Fecha incompleta", "La fecha de nacimiento debe tener el formato DD-MM-AAAA completo.")
                return
            try:
                datetime.strptime(fecha, "%d-%m-%Y")
            except ValueError:
                messagebox.showwarning("Fecha inválida", "Esa fecha no existe, revisa el día y el mes.")
                return

        comunidad = self.fields["comunidad"].get().strip()
        cargo = self.fields["cargo"].get().strip()
        telefono = self.fields["telefono"].get().strip()
        direccion = self.fields["direccion"].get().strip()
        notas = self.notas_text.get("1.0", "end").strip()

        opcionales = [comunidad, cargo, telefono, fecha, direccion, notas]
        if any(not v for v in opcionales):
            if not messagebox.askyesno("Información incompleta", "Falta información, ¿desea continuar?"):
                return

        data = (
            nombre, cedula, comunidad, cargo, telefono, fecha, direccion, notas,
        )

        conn = get_conn()
        if self.current_id:
            conn.execute(
                "UPDATE integrantes SET nombre=?, cedula=?, comunidad=?, cargo=?, telefono=?, "
                "fecha_nacimiento=?, direccion=?, notas=? WHERE id=?",
                data + (self.current_id,)
            )
        else:
            cur = conn.execute(
                "INSERT INTO integrantes (nombre, cedula, comunidad, cargo, telefono, "
                "fecha_nacimiento, direccion, notas) VALUES (?,?,?,?,?,?,?,?)", data
            )
            self.current_id = cur.lastrowid
        conn.commit()
        conn.close()

        self.refresh_list()
        try:
            self.tree.selection_set(self.current_id)
        except tk.TclError:
            pass
        messagebox.showinfo("Guardado", "Información guardada correctamente.")

    def eliminar(self):
        if not self.current_id:
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar este integrante y todos sus documentos?"):
            return
        conn = get_conn()
        conn.execute("DELETE FROM integrantes WHERE id=?", (self.current_id,))
        conn.commit()
        conn.close()

        carpeta = os.path.join(DOCS_DIR, str(self.current_id))
        if os.path.isdir(carpeta):
            shutil.rmtree(carpeta, ignore_errors=True)

        self.limpiar_form()
        self.refresh_list()

    def refresh_docs(self):
        self.doc_list.delete(0, "end")
        if not self.current_id:
            return
        conn = get_conn()
        rows = conn.execute(
            "SELECT nombre_archivo FROM documentos WHERE integrante_id=? ORDER BY id", (self.current_id,)
        ).fetchall()
        conn.close()
        for r in rows:
            self.doc_list.insert("end", r[0])

    def agregar_doc(self):
        if not self.current_id:
            messagebox.showwarning("Primero guarda", "Guarda el integrante antes de agregar documentos.")
            return
        rutas = filedialog.askopenfilenames(title="Selecciona uno o varios documentos")
        if not rutas:
            return

        carpeta = os.path.join(DOCS_DIR, str(self.current_id))
        os.makedirs(carpeta, exist_ok=True)

        conn = get_conn()
        for ruta in rutas:
            nombre_archivo = os.path.basename(ruta)
            destino = os.path.join(carpeta, nombre_archivo)
            if os.path.exists(destino):
                base, ext = os.path.splitext(nombre_archivo)
                nombre_archivo = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
                destino = os.path.join(carpeta, nombre_archivo)
            shutil.copy2(ruta, destino)
            conn.execute(
                "INSERT INTO documentos (integrante_id, nombre_archivo, ruta_relativa, fecha_agregado) "
                "VALUES (?,?,?,?)",
                (self.current_id, nombre_archivo, os.path.join(str(self.current_id), nombre_archivo),
                 datetime.now().isoformat())
            )
        conn.commit()
        conn.close()
        self.refresh_docs()

    def abrir_doc(self):
        sel = self.doc_list.curselection()
        if not sel or not self.current_id:
            return
        nombre_archivo = self.doc_list.get(sel[0])
        ruta = os.path.join(DOCS_DIR, str(self.current_id), nombre_archivo)
        if os.path.exists(ruta):
            abrir_archivo(ruta)
        else:
            messagebox.showerror("No encontrado", "El archivo no existe en el disco.")

    def quitar_doc(self):
        sel = self.doc_list.curselection()
        if not sel or not self.current_id:
            return
        nombre_archivo = self.doc_list.get(sel[0])
        if not messagebox.askyesno("Confirmar", f"¿Quitar el documento '{nombre_archivo}'?"):
            return
        conn = get_conn()
        conn.execute(
            "DELETE FROM documentos WHERE integrante_id=? AND nombre_archivo=?",
            (self.current_id, nombre_archivo)
        )
        conn.commit()
        conn.close()
        ruta = os.path.join(DOCS_DIR, str(self.current_id), nombre_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
        self.refresh_docs()

    def exportar_excel(self):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill
            from openpyxl.utils import get_column_letter
        except ImportError:
            messagebox.showerror(
                "Falta un componente",
                "Para exportar a Excel se necesita instalar 'openpyxl'.\n\n"
                "Abre una terminal en la carpeta del proyecto y ejecuta:\n"
                "pip install openpyxl"
            )
            return

        destino = filedialog.asksaveasfilename(
            title="Exportar a Excel",
            defaultextension=".xlsx",
            initialfile=f"integrantes_cabildo_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            filetypes=[("Libro de Excel", "*.xlsx")]
        )
        if not destino:
            return

        conn = get_conn()
        rows = conn.execute(
            "SELECT nombre, cedula, comunidad, cargo, telefono, fecha_nacimiento, direccion, notas "
            "FROM integrantes ORDER BY nombre"
        ).fetchall()
        conn.close()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Integrantes"
        encabezados = ["Nombre completo", "N° de documento", "Comunidad", "Cargo", "Teléfono",
                       "Fecha de nacimiento", "Dirección", "Notas"]
        ws.append(encabezados)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2F6B4F")

        for row in rows:
            ws.append(list(row))

        anchos = [28, 16, 18, 20, 14, 16, 28, 30]
        for i, ancho in enumerate(anchos, start=1):
            ws.column_dimensions[get_column_letter(i)].width = ancho

        wb.save(destino)
        messagebox.showinfo("Exportado", f"Se exportaron {len(rows)} integrantes a:\n{destino}")

    def crear_respaldo(self):
        destino = filedialog.asksaveasfilename(
            title="Guardar respaldo como...",
            defaultextension=".zip",
            initialfile=f"respaldo_cabildo_{datetime.now().strftime('%Y-%m-%d')}.zip",
            filetypes=[("Archivo ZIP", "*.zip")]
        )
        if not destino:
            return
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(DATA_DIR):
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, DATA_DIR)
                    z.write(full, rel)
        messagebox.showinfo("Respaldo creado", f"Respaldo guardado en:\n{destino}")

    def restaurar_respaldo(self):
        origen = filedialog.askopenfilename(
            title="Selecciona el archivo de respaldo (.zip)",
            filetypes=[("Archivo ZIP", "*.zip")]
        )
        if not origen:
            return
        if not messagebox.askyesno(
            "Confirmar restauración",
            "Esto REEMPLAZARÁ toda la información actual (incluido el PIN) por la del respaldo.\n\n¿Continuar?"
        ):
            return

        if os.path.isdir(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        os.makedirs(DATA_DIR, exist_ok=True)

        with zipfile.ZipFile(origen, "r") as z:
            z.extractall(DATA_DIR)

        os.makedirs(DOCS_DIR, exist_ok=True)
        self.limpiar_form()
        self.refresh_list()
        messagebox.showinfo("Restauración completa", "La información fue restaurada correctamente.")


if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
