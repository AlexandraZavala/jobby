from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Optional

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

class JobResponse(BaseModel):
    id: Optional[str] = ""
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    requirements: str = ""
    benefits: str = ""
    modality: str = ""
    link: str = ""

class QueryResponse(BaseModel):
    query: str
    results: List[JobResponse]
    total: int

class HealthResponse(BaseModel):
    status: str
    message: str

# Variables globales para el vectorstore
vectorstore = None
embeddings = None

def cargar_empleos_formateados():
    """Carga los empleos ya formateados"""
    try:
        with open("jobs_for_chatbot.json", "r", encoding="utf-8") as f:
            empleos = json.load(f)
        print(f"Cargados {len(empleos)} empleos")
        return empleos
    except FileNotFoundError:
        print("No se encontró jobs_for_chatbot.json")
        return []
    except Exception as e:
        print(f"Error cargando: {e}")
        return []

def dividir_documentos(empleos):
    """Divide los empleos en documentos para el vectorstore"""
    documentos = []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    for empleo in empleos:
        # Crear texto completo
        texto_completo = f"""
        Título: {empleo.get('title', '')}
        Empresa: {empleo.get('company', '')}
        Ubicación: {empleo.get('location', '')}
        Descripción: {empleo.get('description', '')}
        Requisitos: {empleo.get('requirements', '')}
        Beneficios: {empleo.get('benefits', '')}
        Modalidad: {empleo.get('modality', '')}
        """
        
        # Dividir en chunks si es necesario
        chunks = text_splitter.split_text(texto_completo.strip())
        
        for chunk in chunks:
            documento = Document(
                page_content=chunk,
                metadata={
                    'title': empleo.get('title', ''),
                    'company': empleo.get('company', ''),
                    'location': empleo.get('location', ''),
                    'description': empleo.get('description', ''),
                    'requirements': empleo.get('requirements', ''),
                    'benefits': empleo.get('benefits', ''),
                    'modality': empleo.get('modality', ''),
                    'link': empleo.get('link', ''),
                    'empleo_id': empleo.get('id', '')
                }
            )
            documentos.append(documento)
    
    print(f"Creados {len(documentos)} documentos")
    return documentos

def inicializar_vectorstore():
    """Inicializa el vectorstore con los empleos"""
    global vectorstore, embeddings
    
    print("Inicializando vectorstore...")
    
    # Cargar empleos
    empleos = cargar_empleos_formateados()
    if not empleos:
        print("No se pudieron cargar empleos")
        return False
    
    # Crear documentos
    documentos = dividir_documentos(empleos)
    if not documentos:
        print("No se pudieron crear documentos")
        return False
    
    # Inicializar embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    # Crear vectorstore
    try:
        vectorstore = Chroma.from_documents(
            documents=documentos,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        print("Vectorstore creado exitosamente")
        return True
    except Exception as e:
        print(f"Error creando vectorstore: {e}")
        return False

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

@app.post("/query_jobs", response_model=QueryResponse)
async def query_jobs(request: QueryRequest):
    """Endpoint principal para consultar empleos"""
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
            empleo_id = metadata.get('empleo_id', '')
            
            # Evitar duplicados
            if empleo_id not in empleos_unicos:
                empleo = JobResponse(
                    id=empleo_id,
                    title=metadata.get('title', ''),
                    company=metadata.get('company', ''),
                    location=metadata.get('location', ''),
                    description=metadata.get('description', ''),
                    requirements=metadata.get('requirements', ''),
                    benefits=metadata.get('benefits', ''),
                    modality=metadata.get('modality', ''),
                    link=metadata.get('link', '')
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
        empleos = cargar_empleos_formateados()
        job_responses = [
            JobResponse(
                id=empleo.get('id', ''),
                title=empleo.get('title', ''),
                company=empleo.get('company', ''),
                location=empleo.get('location', ''),
                description=empleo.get('description', ''),
                requirements=empleo.get('requirements', ''),
                benefits=empleo.get('benefits', ''),
                modality=empleo.get('modality', ''),
                link=empleo.get('link', '')
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
