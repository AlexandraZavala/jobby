from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from collections import defaultdict
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq
from typing import List, Optional

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

# Modelos Pydantic
class ChatRequest(BaseModel):
    mensaje: str

class ChatResponse(BaseModel):
    respuesta: str
    empleos: Optional[List[dict]] = None

class JobDetailResponse(BaseModel):
    job: Optional[dict] = None
    found: bool

class HealthResponse(BaseModel):
    status: str
    message: str


# Variables globales
vectorstore = None
embeddings = None
conversaciones = defaultdict(list)
VECTORSTORE_PATH = "./data/chroma_db"
# Configuración de APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializar clientes
openai_client = None
groq_client = None

if GROQ_API_KEY and GROQ_API_KEY != "tu_api_key_de_groq_aqui":
    groq_client = Groq(api_key=GROQ_API_KEY)

if OPENAI_API_KEY and OPENAI_API_KEY != "tu_api_key_de_openai_aqui":
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def cargar_empleos():
    """Carga los empleos del archivo JSON"""
    try:
        with open("jobs_for_chatbot.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("No se encontró jobs_for_chatbot.json")
        return []


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




def generar_con_groq(prompt: str, modelo: str = "llama-3.1-8b-instant") -> str:
    """Genera texto usando Groq (súper rápido y gratis!)"""
    try:
        response = groq_client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": "Eres un asesor laboral profesional y amable que ayuda a las personas a encontrar empleos. Responde en español de manera clara y útil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error con Groq: {e}")
        raise e

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


@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint raíz"""
    return HealthResponse(
        status="OK", 
        message="Jobby API funcionando correctamente"
    )
@app.on_event("startup")
async def startup_event():
    """Inicializar vectorstore al iniciar el servidor"""
    print("Iniciando servidor FastAPI...")
    if inicializar_vectorstore():
        print("Servidor listo para recibir consultas")
    else:
        print("Error inicializando vectorstore")

@app.get("/health", response_model=HealthResponse)
async def health():
    """Endpoint para verificar que el servidor esté funcionando"""
    return HealthResponse(
        status="OK", 
        message="Servidor funcionando correctamente"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal del chatbot"""
    try:
        pregunta = request.mensaje
        
        if not pregunta:
            raise HTTPException(status_code=400, detail="No se recibió el mensaje")

        # Cargar empleos para contexto
        empleos = cargar_empleos()
        
        # Buscar empleos relevantes usando vectorstore
        if vectorstore is None:
            raise HTTPException(status_code=500, detail="Vectorstore no inicializado")
        
        documentos_relevantes = vectorstore.similarity_search(pregunta, k=3)
        
        # Convertir Documents a diccionarios para que funcione con Pydantic
        empleos_relevantes = []
        empleos_originales = cargar_empleos()  # Cargar empleos originales
        
        for doc in documentos_relevantes:
            # Buscar el empleo original por ID para obtener todos los datos
            empleo_original = None
            empleo_id = doc.metadata.get("id", "")
            
            for emp in empleos_originales:
                if emp.get("id") == empleo_id:
                    empleo_original = emp
                    break
            
            if empleo_original:
                # Usar el empleo original completo
                empleos_relevantes.append(empleo_original)
            else:
                # Crear diccionario desde metadatos si no encontramos el original
                empleo_dict = {
                    "title": doc.metadata.get("title", "Sin título"),
                    "company": doc.metadata.get("company", "Sin empresa"),
                    "location": doc.metadata.get("location", "Sin ubicación"),
                    "id": doc.metadata.get("id", ""),
                    "visual_id": doc.metadata.get("visual_id", ""),
                    "job_type": doc.metadata.get("job_type", ""),
                    "salary_info": doc.metadata.get("salary_info", ""),
                    "description": "Descripción no disponible",
                    "requirements": ""
                }
                empleos_relevantes.append(empleo_dict)

        #print(empleos_relevantes)

        # Crear contexto con empleos relevantes
        contexto = ""
        if empleos_relevantes:
            for i, empleo in enumerate(empleos_relevantes):
                contexto += f"""
Empleo {i+1}:
- Título: {empleo.get('title', 'Sin título')}
- ID: {empleo.get('id', '')}
- Empresa: {empleo.get('company', 'Sin empresa')}
- Ubicación: {empleo.get('location', 'Sin ubicación')}
- Descripción: {empleo.get('description', 'Sin descripción')[:300]}...
"""
        else:
            # Si no hay empleos relevantes, usar algunos empleos generales
            for i, empleo in enumerate(empleos[:3]):
                contexto += f"""
Empleo {i+1}:
- Título: {empleo.get('title', 'Sin título')}
- ID: {empleo.get('id', '')}
- Empresa: {empleo.get('company', 'Sin empresa')}
- Ubicación: {empleo.get('location', 'Sin ubicación')}
- Descripción: {empleo.get('description', 'Sin descripción')[:300]}...
"""
            empleos_relevantes = empleos[:3]

        # Construir prompt contextual
        prompt = f"""
Eres un asesor laboral profesional y conciso. 

Pregunta del usuario: {pregunta}

Contexto: {contexto}

Empleos encontrados: {len(empleos_relevantes)} ofertas relevantes

Instrucciones:
- Responde en máximo 2 oraciones cortas. Con un resumen de lo que encontraste.
- Si no hay empleos relevantes, sugiere buscar con otras palabras clave.
- NO repitas los detalles de los empleos (título, empresa, ubicación) porque ya se muestran en las tarjetas
- Solo da un consejo breve y útil
- Sé directo y no redundante
- SOLO TE ENCARGAS DE RESPONDER EN BASE A LA INFORMACION QUE ENCONTRASTE, NO OFREZCAS OTROS SERVICIOS, SOLO DAS INFORMACION SOBRE LOS EMPLEOS ENCONTRADOS
- SOLO RESUME LO QUE ENCONTRASTE Y NO PREGUNTES O TE OFREZCAS A AYUDAR CON ALGO MÁS, SOLO RESPONDE A LA PREGUNTA DEL USUARIO
- NO RESPONDAS CON NINGUNA PREGUNTA
"""

        # Prioridad: Groq (gratis y rápido) > OpenAI > Fallback
        try:
            if groq_client:
                respuesta = generar_con_groq(prompt)
            elif openai_client:
                respuesta = generar_con_openai(prompt)
            else:
                # Esto no debería pasar, pero por seguridad
                respuesta = f"Encontré {len(empleos_relevantes)} empleos que podrían interesarte. ¿Te llama la atención alguno?"
        except Exception as e:
            print(f"Error con IA: {e}")
            # Fallback sin IA
            respuesta = f"Aquí tienes {len(empleos_relevantes)} empleos relacionados con tu búsqueda. ¿Necesitas ayuda con algo más específico?"

        return ChatResponse(respuesta=respuesta, empleos=empleos_relevantes)
        
    except Exception as e:
        print(f"Error en chat: {e}")
        # Respuesta de emergencia
        empleos = cargar_empleos()
        empleos_fallback = empleos[:3] if empleos else []
        return ChatResponse(
            respuesta="Hola! ¿Qué tipo de trabajo estás buscando? Te ayudo a encontrar las mejores oportunidades.",
            empleos=empleos_fallback
        )

@app.get("/get_all_jobs")
async def get_all_jobs():
    """Endpoint para obtener todos los empleos disponibles"""
    try:
        empleos = cargar_empleos()
        return {
            "results": empleos,
            "total": len(empleos)
        }
    except Exception as e:
        print(f"Error en get_all_jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/{job_id}", response_model=JobDetailResponse)
async def get_job_details(job_id: str):
    """Endpoint para obtener detalles completos de un empleo específico"""
    try:
        empleos = cargar_empleos()
        
        # Buscar el empleo por ID
        empleo_encontrado = None
        for empleo in empleos:
            if empleo.get('id') == job_id or empleo.get('visual_id') == job_id:
                empleo_encontrado = empleo
                break
        
        if empleo_encontrado:
            return JobDetailResponse(job=empleo_encontrado, found=True)
        else:
            return JobDetailResponse(job=None, found=False)
            
    except Exception as e:
        print(f"Error en get_job_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
