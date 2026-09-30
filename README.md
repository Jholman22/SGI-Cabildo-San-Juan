# Sistema de Gestión de Información

Aplicación de escritorio para la administración de integrantes y documentos de un cabildo indígena:
registro de datos personales, almacenamiento de documentos escaneados, búsqueda instantánea, respaldo
completo y exportación a Excel. Funciona 100% local — sin depender de internet ni de servicios externos.

![Plataforma](https://img.shields.io/badge/plataforma-Windows-0078D6)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Licencia](https://img.shields.io/badge/uso-privado-lightgrey)

## Descripción

Este proyecto nació para resolver un problema concreto: centralizar y organizar la información de los
integrantes de un cabildo, que antes se manejaba en carpetas físicas de papeleo. La aplicación permite
registrar cada integrante con sus datos y documentos de soporte (cédulas, certificados, etc.), buscarlos
en segundos, y mantener respaldos seguros de toda la información.

## Características principales

- **Registro completo de integrantes**: nombre, documento de identidad, comunidad, cargo, teléfono,
  fecha de nacimiento (con formato guiado DD-MM-AAAA) y dirección.
- **Gestión de documentos**: adjunta, visualiza y elimina archivos (PDF, imágenes, Word, etc.) asociados
  a cada integrante — se guardan como archivos reales en disco, no como datos binarios en la base de datos.
- **Búsqueda instantánea** por nombre, cédula o comunidad.
- **Acceso protegido con PIN** de 4 dígitos, con opción de cambiarlo desde la pantalla de bloqueo.
- **Exportación a Excel** (.xlsx) de toda la información en cualquier momento.
- **Respaldo y restauración** completos en un solo archivo `.zip` (base de datos + documentos).
- **Interfaz en español**, con autoformato de texto (mayúscula automática tipo oración) y navegación
  ágil con teclado (Enter para avanzar entre campos).
- **Sin dependencias externas para el usuario final**: se distribuye como un único `.exe` para Windows.

## Tecnología

| Componente        | Tecnología             |
|--------------------|-------------------------|
| Lenguaje            | Python 3.9+             |
| Interfaz gráfica    | Tkinter (incluido en Python) |
| Base de datos       | SQLite3 (incluido en Python) |
| Exportación a Excel | [openpyxl](https://openpyxl.readthedocs.io/) |
| Empaquetado a .exe  | [PyInstaller](https://pyinstaller.org/) |

## Estructura del proyecto

```
gestor_cabildo/
├── main.py                # Código fuente de la aplicación
├── requirements.txt       # Dependencias (openpyxl, pyinstaller)
├── assets/
│   ├── icon.ico            # Ícono de la aplicación y del ejecutable
│   └── logo.png            # Logo mostrado en la cabecera de la app
├── INSTALACION.md          # Guía paso a paso: ejecutar, empaquetar y usar la app
└── README.md               # Este archivo
```

## Instalación rápida

```bash
git clone <URL-de-este-repositorio>
cd gestor_cabildo
pip install -r requirements.txt
python main.py
```

Para generar el ejecutable `.exe` (Windows) y para el detalle completo de todas las funcionalidades,
consulta la **[guía de instalación y uso](INSTALACION.md)**.

## Almacenamiento de datos

Toda la información (base de datos SQLite + documentos adjuntos) se guarda localmente en:

```
Documentos/SistemaGestionInformacion/
```

en el computador donde se ejecuta la aplicación. No se envía ni almacena en ningún servidor externo.

## Seguridad

El acceso está protegido con un PIN de 4 dígitos. Esta es una barrera básica pensada para evitar accesos
casuales no autorizados — **no sustituye el cifrado de archivos ni la seguridad de un sistema
multiusuario**. Para escenarios con requisitos de seguridad más estrictos, se recomienda evaluar cifrado
de disco a nivel de sistema operativo (ej. BitLocker en Windows).

## Estado del proyecto

En desarrollo activo — construido a medida para las necesidades de gestión documental de un cabildo
indígena. Sugerencias y mejoras futuras: importación masiva desde Excel, historial de cambios por
integrante, generación automática de certificados en PDF.

## Autor

Desarrollado por Jholman — Ingeniero Electrónico y Analista de Datos.

## Licencia

Proyecto de uso privado, desarrollado a medida para un cliente específico.
