# main.py

import os
from click import prompt
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import requests
from collections import defaultdict  # 👈 AQUÍ
from dotenv import load_dotenv
import json
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from fastapi.responses import PlainTextResponse


load_dotenv()

def cargar_empleos():
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
        "majors": safe_join_lista(empleo.get('majors', [])),  # Convertir lista a string
        "languages": safe_join_lista(empleo.get('languages', [])),  # Convertir lista a string
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


# 🔁 Historial de conversación en memoria (temporal)
conversaciones = defaultdict(list)

# Cargar clave de API de Together.ai desde variables de entorno
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Inicializar FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"mensaje": "Bot Jobly funcionando"}

# CORS (si quieres conectar con frontend o Twilio)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar embeddings y vectorstore
print("🔍 Cargando vectorstore...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
import os

VECTORSTORE_PATH = "./data/chroma_db"

def crear_y_guardar_vectorstore():
    empleos = cargar_empleos()
    documentos = [crear_documento_empleo(e) for e in empleos]

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(documentos)

    vectorstore = Chroma.from_documents(
        chunks,
        embedding=embedding_model,
        persist_directory=VECTORSTORE_PATH
    )
    vectorstore.persist()
    print(f"✅ Vectorstore creado con {len(chunks)} chunks.")
    return vectorstore

# 💡 Cargar o reconstruir según el número real de vectores
try:
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_PATH,
        embedding_function=embedding_model
    )
    cantidad_vectores = vectorstore._collection.count()
    if cantidad_vectores == 0:
        print("⚠️ Vectorstore existente pero vacío. Reconstruyendo...")
        vectorstore = crear_y_guardar_vectorstore()
    else:
        print(f"✅ Vectorstore cargado con {cantidad_vectores} vectores.")
except Exception as e:
    print(f"⚠️ Error al cargar vectorstore: {e}")
    print("🛠 Generando uno nuevo...")
    vectorstore = crear_y_guardar_vectorstore()


# Verifica cuántos documentos tiene
try:
    cantidad = vectorstore._collection.count()
    print(f"📊 El vectorstore contiene {cantidad} vectores")
except Exception as e:
    print(f"⚠️ No se pudo contar los vectores: {e}")


# Función para generar texto con Together.ai
def generar_con_together(prompt: str, modelo: str = "mistralai/Mixtral-8x7B-Instruct-v0.1") -> str:
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

# Endpoint del chatbot
@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    pregunta = body.get("mensaje")

    if not pregunta:
        return {"error": "No se recibió el mensaje"}

    # Buscar los 3 documentos más relevantes
    resultados = vectorstore.similarity_search(pregunta, k=3)
    contexto = "\n\n".join([doc.page_content for doc in resultados])

    # Construir prompt contextual
    prompt = f"""
Eres un asesor laboral profesional y amable. Tienes acceso a una lista de ofertas laborales relevantes extraídas de una base de datos.

Debes responder exclusivamente usando esa información. Si el usuario pregunta por las carreras profesionales para las cuales hay empleos disponibles, analiza los campos 'carreras requeridas' o 'majors' de las ofertas y menciona solo los nombres de las carreras que aparecen.

Luego, pregúntale si le gustaría conocer más detalles sobre alguna de esas opciones.

Ofertas laborales encontradas:

{contexto}

Usuario: {pregunta}
Asesor:
"""


    try:
        respuesta = generar_con_together(prompt)
    except Exception as e:
        return {"error": f"No se pudo generar respuesta: {e}"}

    return {"respuesta": respuesta}

from fastapi import Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse

@app.post("/twilio", response_class=PlainTextResponse)
async def recibir_whatsapp(
    Body: str = Form(...),
    From: str = Form(...)
):
    user_id = From
    conversaciones[user_id].append({"usuario": Body})

    resultados = vectorstore.similarity_search(Body, k=3)
    contexto = "\n\n".join([doc.page_content for doc in resultados])

    historial = conversaciones[user_id][-3:]
    historia_txt = ""
    for turno in historial:
        if "usuario" in turno:
            historia_txt += f"Usuario: {turno['usuario']}\n"
        if "bot" in turno:
            historia_txt += f"Asesor: {turno['bot']}\n"

    prompt = f"""
Actúas como un asesor laboral amable y cercano. Tienes acceso a una lista de ofertas laborales que vienen de una base de datos actualizada.

Responde al usuario utilizando solo la información que aparece en esas ofertas. Si el usuario te pregunta por las carreras para las que hay empleos, revisa las secciones de 'carreras requeridas' y menciona solo las que realmente aparecen. Puedes usar un tono cordial y natural, como si estuvieras conversando para ayudar.

Aquí tienes las ofertas que coinciden con lo que busca el usuario:

{contexto}

Usuario: {Body}
Asesor:
"""


    try:
        respuesta = generar_con_together(prompt)
        if len(respuesta) > 1500:
            respuesta = respuesta[:1450] + "\n\n(Respuesta recortada por límite de mensaje)"
        conversaciones[user_id][-1]["bot"] = respuesta
    except Exception:
        respuesta = "Lo siento, hubo un error generando la respuesta."

    from twilio.twiml.messaging_response import MessagingResponse
    twilio_resp = MessagingResponse()
    twilio_resp.message(respuesta)

    # ❗ DEVOLVER como PlainTextResponse
    return PlainTextResponse(str(twilio_resp), media_type="application/xml")


    

# Para ejecutar localmente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
