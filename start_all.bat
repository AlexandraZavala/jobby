@echo off
echo ===========================================
echo     JOBBY - Iniciando Backend y Frontend
echo ===========================================

echo.
echo 1. Instalando dependencias del backend...
cd back
pip install -r requirements.txt

echo.
echo 2. Iniciando servidor FastAPI...
start cmd /k "uvicorn app:app --host 0.0.0.0 --port 5000 --reload"

echo.
echo 3. Esperando 5 segundos para que inicie el backend...
timeout /t 5

echo.
echo 4. Instalando dependencias del frontend...
cd ../front
npm install

echo.
echo 5. Iniciando servidor frontend...
start cmd /k "npm run dev"

echo.
echo ===========================================
echo     Ambos servidores iniciados
echo     Backend: http://localhost:5000
echo     Frontend: http://localhost:5173
echo     API Docs: http://localhost:5000/docs
echo ===========================================
pause
