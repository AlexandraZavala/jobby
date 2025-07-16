# Jobby - Sistema de Búsqueda Inteligente de Empleos

Este proyecto conecta un backend de FastAPI con LangChain para búsqueda semántica de empleos, con un frontend en React.

## Inicio Rápido

### Opción 1: Iniciar ambos servicios automáticamente
```bash
# Ejecuta este archivo para iniciar backend y frontend
start_all.bat
```

### Opción 2: Iniciar servicios por separado

#### Backend (FastAPI)
```bash
cd back
pip install -r requirements.txt
uvicorn app_simple:app --host 0.0.0.0 --port 5000 --reload
```

#### Frontend (React + Vite)
```bash
cd front
npm install
npm run dev
```

## Endpoints de la API

### Base URL: `http://localhost:5000`

#### 1. Health Check
- **GET** `/health`
- Verifica que el servidor esté funcionando

#### 2. Chat Inteligente (NUEVO)
- **POST** `/chat`
- Body: `{"mensaje": "tu pregunta aquí"}`
- Retorna una respuesta conversacional del asesor laboral usando IA

#### 3. Búsqueda de Empleos
- **POST** `/query_jobs`
- Body: `{"query": "tu búsqueda aquí"}`
- Retorna empleos relevantes usando búsqueda semántica

#### 4. Obtener Todos los Empleos
- **GET** `/get_all_jobs`
- Retorna todos los empleos disponibles

#### 5. Documentación Automática
- **GET** `/docs` - Swagger UI
- **GET** `/redoc` - ReDoc

## Configuración

### Variables de Entorno (Importante)

1. **Configura una API key** en la carpeta `back/.env`:

   **Opción 1: OpenAI (Recomendado)**
   ```
   OPENAI_API_KEY=tu_api_key_de_openai_aqui
   ```
   - Ve a https://platform.openai.com/api-keys
   - Crea una cuenta (tiene plan gratuito)
   - Genera una API key
   - Cópiala en el archivo `.env`

   **Opción 2: Together.ai (Alternativo)**
   ```
   TOGETHER_API_KEY=tu_api_key_de_together_aqui
   ```
   - Ve a https://together.ai/
   - Crea una cuenta gratuita
   - Obtén tu API key

2. **El sistema usa prioridades**:
   - Si tienes OpenAI → Usa ChatGPT
   - Si no hay OpenAI pero hay Together.ai → Usa Together.ai
   - Si no hay ninguna → Chat deshabilitado

### Backend
El backend se inicializa automáticamente y:
1. Carga los empleos desde `jobs_for_chatbot.json`
2. Crea embeddings con HuggingFace
3. Inicializa ChromaDB para búsqueda vectorial
4. Configura el chatbot inteligente (OpenAI ChatGPT preferido, Together.ai como backup)

### Frontend
- Backend URL: `http://localhost:5000`
- Frontend URL: `http://localhost:5173`
- Modo mock: Desactivado (usa backend real)
- Chat inteligente: Activado cuando hay API key configurada

## Uso

1. Inicia ambos servicios con `start_all.bat`
2. Ve a `http://localhost:5173`
3. Escribe tu búsqueda de empleo
4. ¡El sistema te mostrará empleos relevantes!

## Troubleshooting

### Error: "Vectorstore no inicializado"
- Asegúrate de que `jobs_for_chatbot.json` exista en `/back`
- Verifica que las dependencias estén instaladas correctamente

### Error de CORS
- El backend está configurado para permitir conexiones desde localhost:3000 y localhost:5173

### Puerto en uso
- Cambia el puerto en `app.py` si 5000 está ocupado
- Actualiza la URL en `front/src/config/config.js`

## Tecnologías

### Backend
- FastAPI
- LangChain  
- ChromaDB (vector database)
- HuggingFace Embeddings
- OpenAI ChatGPT (principal)
- Together.ai (backup)
- Uvicorn

### Frontend
- React
- Vite
- Axios

## Estructura del Proyecto

```
jobby/
├── back/
│   ├── app.py              # Servidor FastAPI con chat inteligente
│   ├── main2.py            # Implementación original con Twilio
│   ├── .env                # Variables de entorno (API keys)
│   ├── requirements.txt    # Dependencias Python
│   ├── data/               # Datos del vectorstore
│   └── ...
├── front/
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── services/       # API calls (incluye chatWithBot)
│   │   └── config/         # Configuración
│   └── ...
├── start_all.bat          # Inicia ambos servicios
└── start_backend.bat      # Solo backend
```
