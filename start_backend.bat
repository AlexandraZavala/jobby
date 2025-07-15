@echo off
echo ===========================================
echo     JOBBY - Iniciando solo Backend FastAPI
echo ===========================================

cd back
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Iniciando servidor FastAPI...
echo Backend disponible en: http://localhost:5000
echo Documentación automática en: http://localhost:5000/docs
echo.

uvicorn app:app --host 0.0.0.0 --port 5000 --reload
pause
