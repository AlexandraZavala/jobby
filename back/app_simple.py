from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
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

def buscar_empleos_relevantes(query: str, empleos: List[dict], max_resultados: int = 3) -> List[dict]:
    """Busca empleos relevantes basándose en la consulta del usuario"""
    empleos_relevantes = []
    palabras_clave = query.lower().split()
    empleos_vistos = set()  # Para evitar duplicados
    
    # Palabras clave adicionales para diferentes tipos de empleo
    keywords_mapping = {
        'desarrollador': ['developer', 'programador', 'software', 'web', 'frontend', 'backend', 'fullstack'],
        'analista': ['analyst', 'data', 'business', 'datos'],
        'marketing': ['marketing', 'digital', 'social media', 'publicidad'],
        'diseño': ['design', 'diseñador', 'ux', 'ui', 'gráfico'],
        'ventas': ['sales', 'commercial', 'vendedor'],
        'python': ['python', 'django', 'flask', 'pandas'],
        'javascript': ['javascript', 'js', 'react', 'node', 'angular', 'vue'],
        'java': ['java', 'spring', 'hibernate'],
        'practicante': ['intern', 'trainee', 'junior', 'estudiante', 'practice']
    }
    
    # Expandir palabras clave
    expanded_keywords = set(palabras_clave)
    for palabra in palabras_clave:
        if palabra in keywords_mapping:
            expanded_keywords.update(keywords_mapping[palabra])
    
    for empleo in empleos:
        # Crear una clave única para evitar duplicados
        empleo_key = f"{empleo.get('title', '')}-{empleo.get('company', '')}"
        if empleo_key in empleos_vistos:
            continue
        
        titulo = empleo.get('title', '').lower()
        descripcion = empleo.get('description', '').lower()
        empresa = empleo.get('company', '').lower()
        ubicacion = empleo.get('location', '').lower()
        
        # Calcular relevancia
        relevancia = 0
        for keyword in expanded_keywords:
            if keyword in titulo:
                relevancia += 3  # Título tiene más peso
            if keyword in descripcion:
                relevancia += 2
            if keyword in empresa:
                relevancia += 1
            if keyword in ubicacion:
                relevancia += 1
        
        if relevancia > 0:
            empleo_copia = empleo.copy()
            empleo_copia['relevancia'] = relevancia
            empleos_relevantes.append(empleo_copia)
            empleos_vistos.add(empleo_key)
    
    # Ordenar por relevancia y retornar los mejores
    empleos_relevantes.sort(key=lambda x: x['relevancia'], reverse=True)
    return empleos_relevantes[:max_resultados]

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
        
        # Buscar empleos relevantes
        empleos_relevantes = buscar_empleos_relevantes(pregunta, empleos, max_resultados=3)
        
        # Si no hay ninguna API configurada, respuesta simple pero útil
        if not groq_client and not openai_client:
            # Crear respuesta simple
            if empleos_relevantes:
                respuesta = f"Encontré {len(empleos_relevantes)} empleos relevantes para tu búsqueda. ¿Te interesan o necesitas algo más específico?"
            else:
                respuesta = f"Revisé nuestras {len(empleos)} ofertas disponibles. ¿Podrías ser más específico sobre el tipo de trabajo que buscas?"
                empleos_relevantes = empleos[:3]  # Mostrar algunos empleos por defecto
            
            return ChatResponse(respuesta=respuesta, empleos=empleos_relevantes)

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

Empleos encontrados: {len(empleos_relevantes)} ofertas relevantes

Instrucciones:
- Responde en máximo 2 oraciones cortas
- NO repitas los detalles de los empleos (título, empresa, ubicación) porque ya se muestran en las tarjetas
- Solo da un consejo breve y útil
- Pregunta si necesita ayuda con algo específico
- Sé directo y no redundante

Ejemplo de respuesta: "Encontré 3 empleos de análisis de datos que podrían interesarte. Te recomiendo revisar los requisitos de cada uno. ¿Te gustaría que busque algo más específico?"
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
