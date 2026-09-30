# Guía de instalación y uso

> Para una visión general del proyecto, ver el [README principal](README.md).


## ¿Dónde se guarda la información?

- Base de datos: `Documentos/SistemaGestionInformacion/cabildo.db`
- Documentos escaneados: `Documentos/SistemaGestionInformacion/documentos/`

Todo queda en la carpeta **Documentos** del usuario de Windows — no en el navegador, no en archivos
temporales. No depende de que el `.exe` esté en una ruta fija.

## 1. Probar la app en modo desarrollo (sin empaquetar)

Requisitos: Python 3.9 o superior instalado (https://www.python.org/downloads/).
Tkinter y sqlite3 vienen incluidos con Python. Para exportar a Excel también necesitas `openpyxl`:

```bash
pip install openpyxl
```

```bash
python main.py
```

## 2. Convertirla en un .exe de un solo clic

1. Instala PyInstaller (una sola vez):

```bash
pip install pyinstaller
```

2. Desde la carpeta del proyecto, genera el ejecutable (nota el `--add-data`, que empaqueta el ícono y
   el logo dentro del .exe; el separador `;` es específico de Windows):

```bash
pyinstaller --onefile --windowed --name SistemaGestionInformacion --icon=assets/icon.ico --add-data "assets;assets" main.py
```

- `--onefile`: genera un único archivo `.exe` (más fácil de entregar).
- `--windowed`: evita que se abra una consola negra detrás de la ventana.
- `--icon=assets/icon.ico`: usa esa imagen como ícono del archivo .exe (el que se ve en el Explorador).
- `--add-data "assets;assets"`: incluye la carpeta assets (ícono + logo) dentro del ejecutable.

3. El ejecutable queda en la carpeta `dist/SistemaGestionInformacion.exe`. Esa es la que le compartes a tu clienta —
   solo necesita copiar ese archivo a su computador, no necesita tener Python instalado.

## Cambiar el ícono y el logo por los tuyos

En la carpeta `assets/` hay dos archivos de muestra (un diseño genérico verde) que puedes reemplazar:

- `assets/logo.png` → aparece en la cabecera de la app. Recomendado: imagen cuadrada, fondo transparente
  si quieres que se vea integrada (PNG), cualquier tamaño (la app la reduce automáticamente a 48px).
- `assets/icon.ico` → es el ícono del .exe y de la ventana. Debe ser formato `.ico` específicamente
  (no sirve un `.png` renombrado). Para convertir tu imagen a `.ico`, puedes usar una herramienta gratis
  en línea como https://convertio.co/es/png-ico/ o https://icoconvert.com/ — sube tu imagen y descarga
  el `.ico` resultante con ese mismo nombre, reemplazando el archivo en `assets/`.

Después de reemplazar los archivos, vuelve a correr el comando de PyInstaller del paso 2 para generar
un `.exe` nuevo con tu ícono.

## 3. Uso normal

- **PIN de acceso**: la primera vez que se abre la app (en cada computador), pide crear un PIN de 4
  dígitos. Las siguientes veces, pide ingresarlo para entrar. Es una protección básica pensada para que
  alguien no autorizado no abra el programa fácilmente, no es cifrado de los archivos en sí.
- **¿Se te olvidó el PIN?** No hay recuperación automática por ahora. Hay que borrar manualmente el
  archivo `Documentos/SistemaGestionInformacion/config.json` (esto NO borra los datos de los integrantes, solo el
  PIN) y la app pedirá crear uno nuevo la próxima vez que se abra.
- **Autoformato de texto**: en los campos de texto (nombre, comunidad, cargo, dirección y notas), la
  primera letra se pone en mayúscula automáticamente, igual que tras un punto seguido. Los campos de
  cédula, teléfono y fecha no llevan este ajuste porque no aplica.
- **Enter para avanzar**: al escribir en un campo y presionar Enter, el cursor salta directo al
  siguiente campo del formulario, sin necesidad de usar el mouse ni el Tab.
- **Fecha de nacimiento con formato guiado**: el campo muestra "DD-MM-AAAA" como ejemplo dentro del
  cuadro; al escribir, los guiones se insertan solos (solo hay que teclear los números). Al guardar, si
  la fecha está incompleta o no es una fecha real (ej. 31 de febrero), se avisa y no deja guardar.
- **Alerta de información incompleta**: nombre y número de documento siguen siendo obligatorios (no
  deja guardar sin ellos). Si falta cualquier otro dato (comunidad, cargo, teléfono, fecha, dirección o
  notas), pregunta "Falta información, ¿desea continuar?" — si se acepta, guarda igual; si se cancela,
  vuelve al formulario para completarlo.
- **Botón "+ Nuevo integrante"**: disponible tanto en la cabecera (arriba, siempre visible) como en el
  panel de la lista.
- **Exportar a Excel**: menú Archivo → "Exportar a Excel (.xlsx)", o el botón "Exportar a Excel" en el
  panel izquierdo. Genera un archivo .xlsx con todos los integrantes y sus datos, en cualquier momento.
  **Requiere tener instalado `openpyxl`** (ver sección de instalación).
- **Cambiar PIN**: en la pantalla de bloqueo (cuando ya existe un PIN creado), hay un botón "Cambiar
  PIN" que pide el PIN actual + el nuevo PIN dos veces, y lo actualiza.
- **Nuevo integrante**: llena el formulario (nombre y documento son obligatorios) y da clic en Guardar.
- **Buscar**: escribe en el cuadro de búsqueda; filtra por nombre, cédula o comunidad en tiempo real.
- **Documentos**: primero guarda el integrante, luego usa "Agregar..." para adjuntar archivos
  (PDF, Word, imágenes, lo que sea). Doble clic sobre un documento, o el botón "Abrir", lo abre con el
  programa predeterminado de Windows (Adobe, Word, Visor de fotos, etc.) — no hay que "descargar" nada,
  ya es un archivo real en el disco.
- **Respaldo**: menú Archivo → "Crear respaldo (.zip)". Genera un único .zip con todo (base de datos +
  documentos). Recomendado hacerlo cada semana o después de cargar varios integrantes.
- **Restaurar**: menú Archivo → "Restaurar respaldo (.zip)". Útil si cambia de computador: solo hay que
  copiar el .exe al equipo nuevo y restaurar el respaldo ahí.

## Notas técnicas para mantenimiento futuro

- El código está en un solo archivo (`main.py`) para simplicidad; si crece mucho se puede separar en
  módulos (`db.py`, `ui.py`, etc.).
- La base de datos es SQLite estándar — se puede abrir con cualquier herramienta como DB Browser for
  SQLite si necesitas revisar los datos manualmente.
- Los documentos NO se guardan dentro de la base de datos (a diferencia de la versión HTML anterior);
  se guardan como archivos reales organizados en carpetas por ID de integrante
  (`documentos/<id>/archivo.pdf`), y la base de datos solo guarda la referencia. Esto es mucho más
  eficiente para archivos grandes o muchos documentos.
