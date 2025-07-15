@echo off
echo ===========================================
echo     JOBBY - Iniciando Backend FastAPI
echo ===========================================

cd back
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo IMPORTANTE: Configura tu API key en el archivo .env
echo.
echo Opciones disponibles:
echo 1. OpenAI (ChatGPT) - Recomendado
echo    - Ve a: https://platform.openai.com/api-keys
echo    - Crea una API key
echo    - Edita back/.env y pon: OPENAI_API_KEY=tu_api_key_real
echo.
echo 2. Together.ai (Alternativo)
echo    - Ve a: https://together.ai/
echo    - Obtén API key gratuita
echo    - Edita back/.env y pon: TOGETHER_API_KEY=tu_api_key_real
echo.

echo Iniciando servidor FastAPI...
echo Backend disponible en: http://localhost:5000
echo Documentación automática en: http://localhost:5000/docs
echo Endpoint de chat inteligente: POST http://localhost:5000/chat
echo.

uvicorn app:app --host 0.0.0.0 --port 5000 --reload
pause
