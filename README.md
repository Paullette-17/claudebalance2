# Sistema Contable — versión PySide6

Conversión a escritorio (PySide6) del sistema contable web original
(`index.html` + `app24.js` + `styles.css`).

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar

1. No hay que instalar ni configurar nada más: la base de datos SQLite (`cloud_balance.db`) se crea sola, junto a los `.py`, la primera vez que se abre el sistema.
2. Entra con el Administrador inicial (usuario `admin`, contraseña `Admin123`) y crea los demás usuarios desde la página **Usuarios**.
3. Arranca desde el login (NO desde `main.py`, que necesita sesión iniciada):

```bash
python login.py
```

## Estructura (dividido por función, como en el original)

| Archivo               | Función (equivalente en app24.js)                              |
|------------------------|------------------------------------------------------------------|
| `main.py`              | Ventana principal, sidebar, proyectos, tema y cerrar sesión      |
| `ciclo_mensual.py`     | Ventana "Ciclo mensual": lista de carpetas, abrir/crear/renombrar |
| `modelos.py`           | Estado de la app + lógica contable (saldos, calcBalance)         |
| `utilidades.py`        | fmt, uid, today, paleta de colores y estilos Qt (QSS)             |
| `almacenamiento.py`    | Persistencia local en JSON (equivalente a localStorage)          |
| `dashboard.py`         | Página Inicio — tarjetas resumen + gráficas (matplotlib)         |
| `cuentas.py`           | Página Cuentas — alta con código de catálogo, edición, eliminación |
| `diario.py`            | Página Libro Diario — asientos y partidas Debe/Haber              |
| `mayor.py`             | Página Libro Mayor — cuentas T                                    |
| `bg.py`                | Página Balance General                                            |
| `er.py`                | Página Estado de Resultados                                       |
| `analisis.py`          | Página Análisis Financiero — ratios                               |
| `timeline.py`          | Página Historial cronológico                                      |
| `login.py`             | Inicio de sesión (punto de entrada) con selector de rol           |
| `usuarios.py`          | Página Usuarios (solo Administrador) — lista y crea usuarios      |
| `registro.py`          | Ventana "Crear usuario", se abre desde usuarios.py                 |
| `roles.py`             | Roles (Administrador / Operador) y permisos                      |
| `db.py`                | Acceso a SQLite: usuarios, proyectos, cuentas, asientos, partidas |
| `exportar_excel.py`    | Exportación a Excel (openpyxl) y PDF (QPrinter)                   |

## Proyectos y código de cuenta

- El botón **📅 Ciclo mensual** (arriba a la derecha, junto al botón de tema claro/oscuro)
  abre una ventana con todas las carpetas (proyectos) creadas. Desde ahí se puede
  **abrir** una carpeta (doble clic o botón *Abrir*), **crear una nueva** (➕ Nueva carpeta)
  o **renombrar** la seleccionada. Arriba a la izquierda se muestra cuál está abierta.
  Cada carpeta tiene sus propias cuentas y asientos (se guardan en la tabla `proyectos`).
- Al crear o editar una cuenta se puede escribir su **código** del catálogo (ej. `1101`).
  Es opcional y no se puede repetir dentro del mismo proyecto.
- Si tu base de datos es de la versión anterior, no hace falta correr SQL: `db.py`
  la actualiza sola al abrir la app y tus datos quedan en "Proyecto 1".
- El botón **🚪 Cerrar sesión** (abajo en la barra lateral) vuelve a la pantalla de login.

## Notas de la conversión

- El `localStorage` del navegador se reemplaza por un archivo JSON en
  `~/.sistema_contable/datos.json`.
- Las gráficas de Chart.js se reemplazan por `matplotlib` embebido con
  `FigureCanvasQTAgg`.
- La exportación con `xlsx-js-style` se reemplaza por `openpyxl`
  (misma idea: colores de sección, subtotales resaltados, formato de moneda).
- El toggle de tema claro/oscuro cambia la hoja de estilos Qt (QSS)
  completa, igual que las variables CSS del original.
- Cada página se conecta a la señal `estado.cambiado` para refrescarse
  automáticamente cuando cambian los datos (equivalente a llamar
  `renderX()` tras cada acción en JS).

## Exportar / respaldar

Todos los datos viven en un único archivo, `cloud_balance.db` (en la misma carpeta que los `.py`). Para llevar el sistema a otra computadora, copia la carpeta `src` completa (incluido ese archivo).

## Crear el ejecutable (.exe) para otras computadoras

En Windows, con Python instalado, haz doble clic en `build_exe.bat`
(o ejecuta `pyinstaller --noconsole --name CloudBalance --add-data "logo.png;." login.py`).
El programa queda en `dist\CloudBalance\CloudBalance.exe`; comprime esa carpeta
completa en un `.zip` para compartirla. La otra computadora no necesita Python ni VS Code.

Dentro del `.exe` la base de datos se guarda en `%APPDATA%\CloudBalance\cloud_balance.db`
(ejecutando los `.py` sigue estando junto a los archivos). Para mover tus datos, copia ese archivo.
