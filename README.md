# JOBLY - Sistema de Búsqueda Inteligente de Empleos

Sistema completo de búsqueda de empleos que incluye web scraping de LinkedIn, API inteligente con FastAPI, y frontend interactivo en React.

## 🚀 Inicio Rápido

### Opción 1: Iniciar todo automáticamente
```bash
# Ejecuta ambos servicios (backend + frontend)
start_all.bat

# Solo backend
start_backend.bat

# Solo scraper de empleos
start_scraper.bat
```

### Opción 2: Iniciar servicios manualmente

#### Backend (FastAPI)
```bash
cd back
pip install -r requirements.txt
python app_simple.py
```

#### Frontend (React + Vite)
```bash
cd front
npm install
npm run dev
```

#### Scraper de Empleos
```bash
cd back
python scrapping/scrap_all.py
```

## 🛠️ Estructura del Proyecto

```
TRY3/
├── back/                           # Backend FastAPI
│   ├── app_simple.py              # API principal con chatbot
│   ├── requirements.txt           # Dependencias Python
│   ├── .env                       # Variables de entorno
│   ├── scrapping/                 # Sistema de web scraping
│   │   ├── scrap_all.py          # Scraper principal (LinkedIn)
│   │   ├── alljobs_scrap.py      # Extractor de listado de empleos
│   │   └── detailedjobs_scrap.py # Extractor de detalles
│   ├── old_versions/              # Versiones anteriores
│   │   ├── app.py                # API con LangChain completo
│   │   ├── main.py               # Implementación original
│   │   └── main2.py              # Versión con Twilio
│   ├── data/                      # Datos de ChromaDB
│   │   └── chroma_db/
│   ├── jobs_raw.json             # Empleos extraídos (crudo)
│   ├── detalles_empleos.json     # Detalles completos
│   └── jobs_for_chatbot.json     # Datos formateados para API
├── front/                         # Frontend React
│   ├── src/
│   │   ├── components/           # Componentes React
│   │   │   ├── ChatBox.jsx      # Chat principal
│   │   │   ├── JobCard.jsx      # Tarjeta de empleo
│   │   │   ├── JobDetailModal.jsx # Modal de detalles
│   │   │   ├── LoadingSpinner.jsx # Spinner de carga
│   │   │   └── SuggestedQueries.jsx # Consultas sugeridas
│   │   ├── pages/
│   │   │   └── HomePage.jsx     # Página principal
│   │   ├── services/
│   │   │   └── api.js           # Llamadas a la API
│   │   └── config/
│   │       └── config.js        # Configuración
│   ├── package.json
│   └── vite.config.js
├── start_all.bat                  # Inicia backend + frontend
├── start_backend.bat             # Solo backend
├── start_scraper.bat             # Solo scraper
└── README.md                     # Esta documentación
```

## 📡 API Endpoints

### Base URL: `http://localhost:5000`

#### 1. Chatbot Inteligente
- **POST** `/chat`
- Body: `{"mensaje": "tu pregunta aquí"}`
- Respuesta: `{"respuesta": "...", "empleos": [...]}`
- Utiliza OpenAI o Groq para respuestas inteligentes

#### 2. Detalles de Empleo
- **GET** `/job/{job_id}`
- Retorna detalles completos de un empleo específico

#### 3. Todos los Empleos
- **GET** `/get_all_jobs`
- Retorna todos los empleos disponibles

#### 4. Health Check
- **GET** `/health`
- Verifica que el servidor esté funcionando

#### 5. Documentación Automática
- **GET** `/docs` - Swagger UI
- **GET** `/redoc` - ReDoc

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la carpeta `back/`:

```env
# Para el chatbot inteligente (elige una)
OPENAI_API_KEY=tu_api_key_de_openai_aqui
GROQ_API_KEY=tu_api_key_de_groq_aqui

# Para web scraping de Bolsa PUCP
EMAIL=tu_usuario
PASSWORD=tu_contraseña
```

### 2. APIs Disponibles

**Prioridad para el chatbot:**
1. **Groq** (Gratuito y rápido) - Recomendado
2. **OpenAI** (Potente pero de pago)
3. **Fallback** sin IA (respuestas simples)

**Para obtener API keys:**
- **Groq**: https://groq.com/ (Gratuito)
- **OpenAI**: https://platform.openai.com/api-keys

### 3. Dependencias

#### Backend
```bash
cd back
pip install fastapi uvicorn python-dotenv openai groq selenium webdriver-manager
```

#### Frontend
```bash
cd front
npm install
```

## 🔄 Flujo de Trabajo

### 1. Extracción de Datos (Scraping)
```bash
# Ejecutar scraper
start_scraper.bat

# Archivos generados:
# - jobs_raw.json (datos crudos)
# - detalles_empleos.json (detalles completos)  
# - jobs_for_chatbot.json (datos para API)
```

### 2. Ejecutar API
```bash
# Backend carga automáticamente jobs_for_chatbot.json
start_backend.bat
```

### 3. Usar Frontend
```bash
# Frontend conecta automáticamente con el backend
# Ve a http://localhost:5173
```

## 🌟 Características

### Web Scraping
- ✅ Extracción automática de empleos de LinkedIn
- ✅ Selenium en modo headless
- ✅ Manejo automático de ChromeDriver
- ✅ Extracción de detalles completos

### API Inteligente  
- ✅ Chatbot conversacional con IA
- ✅ Búsqueda semántica de empleos
- ✅ Respuestas contextuales
- ✅ Múltiples proveedores de IA

### Frontend Moderno
- ✅ Interfaz React moderna
- ✅ Chat en tiempo real
- ✅ Tarjetas de empleos interactivas
- ✅ Modal de detalles completos
- ✅ Consultas sugeridas

## 🐛 Troubleshooting

### Error: "No se encuentra jobs_for_chatbot.json"
- Ejecuta el scraper primero: `start_scraper.bat`

### Error: "No se encuentra .env"
- Crea el archivo `.env` en `back/` con las credenciales

### Error de Chrome/Selenium
- El sistema instala ChromeDriver automáticamente
- Asegúrate de tener Chrome instalado

### Error de puerto ocupado
- Backend: Cambia el puerto en `app_simple.py`
- Frontend: Cambia en `vite.config.js`

### Error de CORS
- El backend está configurado para localhost:3000 y localhost:5173

## 💻 URLs del Sistema

- **Frontend**: http://localhost:5173
- **API Backend**: http://localhost:5000
- **Documentación API**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## 🔧 Tecnologías

### Backend
- **FastAPI** - Framework web
- **OpenAI/Groq** - Inteligencia artificial
- **Selenium** - Web scraping
- **Python-dotenv** - Variables de entorno

### Frontend  
- **React** - Framework UI
- **Vite** - Build tool
- **CSS3** - Estilos modernos

### Scraping
- **Selenium WebDriver** - Automatización web
- **ChromeDriver** - Navegador headless
- **LinkedIn** - Fuente de datos

---

## 📝 Notas de Desarrollo

- El proyecto usa `app_simple.py` como API principal
- Las versiones anteriores están en `old_versions/`
- El scraper funciona en modo headless (sin ventana)
- Los datos se almacenan en archivos JSON locales
