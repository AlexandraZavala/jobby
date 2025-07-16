@echo off
echo ====================================
echo    INICIANDO SCRAPER DE EMPLEOS
echo ====================================
echo.

REM Cambiar al directorio del backend
cd /d "%~dp0back"

echo Ejecutando scraper...
echo.

python scrapping\scrap_all.py

REM Verificar si el scraping fue exitoso
if errorlevel 1 (
    echo.
    echo El scraper termino con errores
    echo Revisa los mensajes de error arriba
) else (
    echo.
    echo Scraper completado exitosamente!
    echo Revisa los archivos generados:
    echo    - jobs_raw.json
    echo    - detalles_empleos.json  
    echo    - jobs_for_chatbot.json
)

echo.
echo Presiona cualquier tecla para salir...
pause >nul 