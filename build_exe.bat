@echo off
REM ============================================================
REM  Genera el ejecutable de Cloud Balance (solo en Windows).
REM  Doble clic en este archivo, con Python instalado en esta PC.
REM  Resultado: dist\CloudBalance\CloudBalance.exe
REM ============================================================
cd /d "%~dp0"
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --noconsole --name CloudBalance --add-data "logo.png;." login.py
echo.
echo Listo. Comprime la carpeta dist\CloudBalance en un .zip para compartirla.
pause
