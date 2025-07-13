# Sistema de Scraping y Vectorización de Empleos

Este sistema automatiza la extracción de empleos de la plataforma PUCP-CSM, los formatea y los almacena en un vector store para búsquedas semánticas.

## 🚀 Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno:**
Crea un archivo `.env` con:
```env
# Credenciales para el scraping
EMAIL=tu_email@ejemplo.com
PASSWORD=tu_password

# API Key de OpenAI para embeddings
OPENAI_API_KEY=tu_openai_api_key_aqui
```

## 📁 Estructura del Proyecto

- `scrap_all.py` - Script principal de scraping y formateo
- `main.py` - Pipeline completo (scraping + vectorización)
- `format_jobs_for_chatbot.py` - Formateo independiente (opcional)
- `jobs_for_chatbot.json` - Empleos formateados
- `chroma_db/` - Vector store persistido

## 🎯 Uso

### Opción 1: Pipeline Completo (Recomendado)
```bash
python main.py
```

Este comando ejecuta:
1. ✅ Scraping de empleos
2. ✅ Formateo de datos
3. ✅ Creación de documentos LangChain
4. ✅ División en chunks
5. ✅ Vectorización con Chroma

### Opción 2: Solo Scraping y Formateo
```bash
python scrap_all.py
```

### Opción 3: Solo Formateo (si ya tienes datos)
```bash
python format_jobs_for_chatbot.py
```

## 📊 Archivos Generados

- `jobs_raw.json` - Datos crudos del scraping
- `detalles_empleos.json` - Detalles completos de cada empleo
- `jobs_for_chatbot.json` - Empleos formateados para chatbot
- `chroma_db/` - Vector store para búsquedas semánticas

## 🔍 Uso del Vector Store

Una vez creado, puedes usar el vector store para búsquedas:

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Cargar vector store
embeddings = OpenAIEmbeddings()
vector_store = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# Buscar empleos similares
results = vector_store.similarity_search("desarrollador python", k=5)
for doc in results:
    print(f"Título: {doc.metadata['title']}")
    print(f"Empresa: {doc.metadata['company']}")
    print("---")
```

## ⚙️ Configuración

### Chunks de Texto
En `main.py` puedes ajustar:
- `chunk_size=1000` - Tamaño de cada chunk
- `chunk_overlap=200` - Superposición entre chunks

### Embeddings
El sistema usa OpenAI embeddings por defecto. Puedes cambiar a otros proveedores modificando la función `crear_vector_store()`.

## 🛠️ Solución de Problemas

### Error de API Key
```
❌ Error creando vector store: Invalid API key
```
**Solución:** Verifica que tu `OPENAI_API_KEY` esté configurada correctamente.

### Error de Credenciales
```
❌ Error: Las variables EMAIL y PASSWORD deben estar definidas
```
**Solución:** Verifica tu archivo `.env` con las credenciales correctas.

### Error de Dependencias
```
ModuleNotFoundError: No module named 'langchain'
```
**Solución:** Ejecuta `pip install -r requirements.txt`

## 📈 Estadísticas

El sistema genera estadísticas automáticamente:
- Número de empleos procesados
- Empresas únicas
- Ubicaciones únicas
- Chunks generados

## 🔄 Actualización

Para actualizar los datos:
1. Ejecuta `python main.py` nuevamente
2. El vector store se sobrescribirá con datos frescos

## 📝 Notas

- El scraping puede tomar varios minutos dependiendo del número de empleos
- Asegúrate de tener una conexión estable a internet
- El vector store se guarda localmente en `./chroma_db`
- Los datos originales se preservan en los archivos JSON 