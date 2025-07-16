from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import requests
from collections import defaultdict
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Optional
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI(
    title="Jobby API",
    description="API para búsqueda inteligente de empleos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para requests/responses
class QueryRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    mensaje: str

class JobResponse(BaseModel):
    id: Optional[str] = ""
    visual_id: Optional[str] = ""
    title: str = ""
    company: str = ""
    location: str = ""
    job_type: str = ""
    salary_info: str = ""
    description: str = ""
    requirements: str = ""
    contact_email: str = ""
    remote_type: str = ""
    experience_level: str = ""
    education_level: str = ""
    majors: str = ""
    languages: str = ""
    vacancies: str = ""
    hours_per_week: str = ""
    start_date: str = ""
    end_date: str = ""

class QueryResponse(BaseModel):
    query: str
    results: List[JobResponse]
    total: int

class ChatResponse(BaseModel):
    respuesta: str

class HealthResponse(BaseModel):
    status: str
    message: str

# Variables globales
vectorstore = None
embeddings = None
conversaciones = defaultdict(list)

# Configuración de APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")  # Backup
VECTORSTORE_PATH = "./data/chroma_db"

# Inicializar cliente OpenAI
openai_client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "tu_api_key_de_openai_aqui":
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def cargar_empleos():
    """Carga los empleos del archivo JSON"""
    with open("jobs_for_chatbot.json", "r", encoding="utf-8") as f:
        return json.load(f)

def crear_documento_empleo(empleo):
    """Crea un documento LangChain para un empleo individual"""
    
    # Función auxiliar para manejar listas con valores None
    def safe_join_lista(lista, separador=", "):
        if not lista:
            return "No especificado"
        # Filtrar valores None y convertir a string
        elementos_limpios = [str(item) for item in lista if item is not None and str(item).strip()]
        return separador.join(elementos_limpios) if elementos_limpios else "No especificado"
    
    # Crear contenido del documento
    contenido = f"""
    Título: {empleo.get('title', 'Sin título')}
    Empresa: {empleo.get('company', 'Sin empresa')}
    Ubicación: {empleo.get('location', 'Sin ubicación')}
    Tipo de empleo: {empleo.get('job_type', 'Sin especificar')}
    Salario: {empleo.get('salary_info', 'No especificado')}

    Descripción:
    {empleo.get('description', 'Sin descripción')}

    Requisitos:
    {empleo.get('requirements', 'Sin requisitos')}

    Información adicional:
    - Email: {empleo.get('contact_email', 'No especificado')}
    - Remoto: {empleo.get('remote_type', 'No especificado')}
    - Nivel de experiencia: {empleo.get('experience_level', 'No especificado')}
    - Nivel de educación: {empleo.get('education_level', 'No especificado')}
    - Carreras requeridas: {safe_join_lista(empleo.get('majors', []))}
    - Idiomas: {safe_join_lista(empleo.get('languages', []))}
    - Número de vacantes: {empleo.get('vacancies', 'No especificado')}
    - Horas por semana: {empleo.get('hours_per_week', 'No especificado')}
    """

    # Crear metadatos para el documento
    metadatos = {
        "id": empleo.get('id', ''),
        "visual_id": empleo.get('visual_id', ''),
        "title": empleo.get('title', ''),
        "company": empleo.get('company', ''),
        "location": empleo.get('location', ''),
        "job_type": empleo.get('job_type', ''),
        "salary_info": empleo.get('salary_info', ''),
        "contact_email": empleo.get('contact_email', ''),
        "remote_type": empleo.get('remote_type', ''),
        "experience_level": empleo.get('experience_level', ''),
        "education_level": empleo.get('education_level', ''),
        "majors": safe_join_lista(empleo.get('majors', [])),
        "languages": safe_join_lista(empleo.get('languages', [])),
        "vacancies": empleo.get('vacancies', ''),
        "hours_per_week": empleo.get('hours_per_week', ''),
        "start_date": empleo.get('start_date', ''),
        "end_date": empleo.get('end_date', ''),
        "tipo_documento": "empleo"
    }
    
    return Document(
        page_content=contenido.strip(),
        metadata=metadatos
    )

def crear_y_guardar_vectorstore():
    """Crea y guarda el vectorstore"""
    empleos = cargar_empleos()
    documentos = [crear_documento_empleo(e) for e in empleos]

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100,length_function=len,
            separators=["\n\n", "\n", " ", ""])
    chunks = splitter.split_documents(documentos)

    vectorstore = Chroma.from_documents(
        chunks,
        embedding=embeddings,
        persist_directory=VECTORSTORE_PATH
    )
    vectorstore.persist()
    print(f"Vectorstore creado con {len(chunks)} chunks.")
    return vectorstore

def inicializar_vectorstore():
    """Inicializa el vectorstore con los empleos"""
    global vectorstore, embeddings
    
    print("Inicializando vectorstore...")
    
    # Inicializar embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    # Cargar o crear vectorstore
    try:
        vectorstore = Chroma(
            persist_directory=VECTORSTORE_PATH,
            embedding_function=embeddings
        )
        cantidad_vectores = vectorstore._collection.count()
        if cantidad_vectores == 0:
            print("Vectorstore existente pero vacío. Reconstruyendo...")
            vectorstore = crear_y_guardar_vectorstore()
        else:
            print(f"Vectorstore cargado con {cantidad_vectores} vectores.")
    except Exception as e:
        print(f"Error al cargar vectorstore: {e}")
        print("Generando uno nuevo...")
        vectorstore = crear_y_guardar_vectorstore()
    
    # Verificar cuántos documentos tiene
    try:
        cantidad = vectorstore._collection.count()
        print(f"El vectorstore contiene {cantidad} vectores")
        return True
    except Exception as e:
        print(f"No se pudo contar los vectores: {e}")
        return False

def generar_con_openai(prompt: str, modelo: str = "gpt-3.5-turbo") -> str:
    """Genera texto usando OpenAI ChatGPT"""
    try:
        response = openai_client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": "Eres un asesor laboral profesional y amable que ayuda a las personas a encontrar empleos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error con OpenAI: {e}")
        raise e

def generar_con_together(prompt: str, modelo: str = "mistralai/Mixtral-8x7B-Instruct-v0.1") -> str:
    """Genera texto usando Together.ai (backup)"""
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@app.on_event("startup")
async def startup_event():
    """Inicializar vectorstore al iniciar el servidor"""
    print("Iniciando servidor FastAPI...")
    if inicializar_vectorstore():
        print("Servidor listo para recibir consultas")
    else:
        print("Error inicializando vectorstore")

@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint raíz"""
    return HealthResponse(
        status="OK", 
        message="Jobby API funcionando correctamente"
    )

@app.get("/health", response_model=HealthResponse)
async def health():
    """Endpoint para verificar que el servidor esté funcionando"""
    return HealthResponse(
        status="OK", 
        message="Servidor funcionando correctamente"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal del chatbot - similar a main2.py pero para frontend"""
    try:
        pregunta = request.mensaje
        
        if not pregunta:
            raise HTTPException(status_code=400, detail="No se recibió el mensaje")

        # Verificar que el vectorstore esté inicializado
        if vectorstore is None:
            raise HTTPException(status_code=500, detail="Vectorstore no inicializado")

        # Buscar los 3 documentos más relevantes
        resultados = vectorstore.similarity_search(pregunta, k=3)
        contexto = "\n\n".join([doc.page_content for doc in resultados])
        print(f"Contexto encontrado: {contexto[:200]}...")  # Mostrar solo los primeros 200 caracteres para depuración

        # Construir prompt contextual (igual que en main2.py)
        prompt = f"""
Eres un asesor laboral profesional y amable. Tienes acceso a una lista de ofertas laborales relevantes extraídas de una base de datos.

Debes responder exclusivamente usando esa información. 

Solo si el usuario pregunta por las carreras profesionales para las cuales hay empleos disponibles, analiza los campos 'carreras requeridas' o 'majors' de las ofertas y menciona solo los nombres de las carreras que aparecen.

Luego, pregúntale si le gustaría conocer más detalles sobre alguna de esas opciones.

Si el usuario pregunta por algo que no tienen nada que ver con ofertas laborales, responde que no tienes información sobre eso.

Solo responde con información relacionada con las ofertas laborales. Usa el idioma español, si el usuario usa otro idioma no respondas.

Ofertas laborales encontradas:

{contexto}

Usuario: {pregunta}
Asesor:
"""

        # Generar respuesta con OpenAI (prioridad) o Together.ai (backup)
        if openai_client:
            try:
                respuesta = generar_con_openai(prompt)
            except Exception as e:
                print(f"Error con OpenAI, intentando con Together.ai: {e}")
                if TOGETHER_API_KEY and TOGETHER_API_KEY != "tu_api_key_aqui":
                    try:
                        respuesta = generar_con_together(prompt)
                    except Exception as e2:
                        raise HTTPException(status_code=500, detail=f"Error en ambos servicios de IA: OpenAI: {e}, Together.ai: {e2}")
                else:
                    raise HTTPException(status_code=500, detail=f"Error con OpenAI y no hay Together.ai configurado: {e}")
        elif TOGETHER_API_KEY and TOGETHER_API_KEY != "tu_api_key_aqui":
            try:
                respuesta = generar_con_together(prompt)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error generando respuesta con Together.ai: {e}")
        else:
            # Sin ninguna API configurada
            respuesta = "Lo siento, el servicio de chat inteligente no está disponible. Por favor, configura una API key de OpenAI o Together.ai en el archivo .env"

        return ChatResponse(respuesta=respuesta)
        
    except Exception as e:
        print(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query_jobs", response_model=QueryResponse)
async def query_jobs(request: QueryRequest):
    """Endpoint para búsqueda directa de empleos (mantener compatibilidad)"""
    try:
        query = request.query
        
        # Verificar que el vectorstore esté inicializado
        if vectorstore is None:
            raise HTTPException(status_code=500, detail="Vectorstore no inicializado")
        
        # Buscar empleos similares
        resultados = vectorstore.similarity_search(query, k=5)
        
        # Formatear resultados
        empleos_encontrados = []
        empleos_unicos = set()
        
        for doc in resultados:
            metadata = doc.metadata
            empleo_id = metadata.get('id', '')
            
            # Evitar duplicados
            if empleo_id not in empleos_unicos:
                empleo = JobResponse(
                    id=empleo_id,
                    visual_id=metadata.get('visual_id', ''),
                    title=metadata.get('title', ''),
                    company=metadata.get('company', ''),
                    location=metadata.get('location', ''),
                    job_type=metadata.get('job_type', ''),
                    salary_info=metadata.get('salary_info', ''),
                    description=metadata.get('description', ''),
                    requirements=metadata.get('requirements', ''),
                    contact_email=metadata.get('contact_email', ''),
                    remote_type=metadata.get('remote_type', ''),
                    experience_level=metadata.get('experience_level', ''),
                    education_level=metadata.get('education_level', ''),
                    majors=metadata.get('majors', ''),
                    languages=metadata.get('languages', ''),
                    vacancies=metadata.get('vacancies', ''),
                    hours_per_week=metadata.get('hours_per_week', ''),
                    start_date=metadata.get('start_date', ''),
                    end_date=metadata.get('end_date', '')
                )
                empleos_encontrados.append(empleo)
                empleos_unicos.add(empleo_id)
        
        return QueryResponse(
            query=query,
            results=empleos_encontrados,
            total=len(empleos_encontrados)
        )
        
    except Exception as e:
        print(f"Error en query_jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_all_jobs")
async def get_all_jobs():
    """Endpoint para obtener todos los empleos disponibles"""
    try:
        empleos = cargar_empleos()
        job_responses = [
            JobResponse(
                id=empleo.get('id', ''),
                visual_id=empleo.get('visual_id', ''),
                title=empleo.get('title', ''),
                company=empleo.get('company', ''),
                location=empleo.get('location', ''),
                job_type=empleo.get('job_type', ''),
                salary_info=empleo.get('salary_info', ''),
                description=empleo.get('description', ''),
                requirements=empleo.get('requirements', ''),
                contact_email=empleo.get('contact_email', ''),
                remote_type=empleo.get('remote_type', ''),
                experience_level=empleo.get('experience_level', ''),
                education_level=empleo.get('education_level', ''),
                majors=", ".join(empleo.get('majors', [])) if empleo.get('majors') else '',
                languages=", ".join(empleo.get('languages', [])) if empleo.get('languages') else '',
                vacancies=empleo.get('vacancies', ''),
                hours_per_week=empleo.get('hours_per_week', ''),
                start_date=empleo.get('start_date', ''),
                end_date=empleo.get('end_date', '')
            ) for empleo in empleos
        ]
        
        return {
            "results": job_responses,
            "total": len(job_responses)
        }
    except Exception as e:
        print(f"Error en get_all_jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
