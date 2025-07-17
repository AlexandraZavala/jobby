import os
import uvicorn
import json
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from collections import defaultdict
from dotenv import load_dotenv
from groq import Groq

# ===================== CONFIGURACIÓN =====================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("No se encontró GROQ_API_KEY en el .env")
client = Groq(api_key=GROQ_API_KEY)

VECTORSTORE_PATH = "./data/chroma_db_jobs"

# Conversaciones en memoria: historial y contexto
conversaciones = defaultdict(lambda: {
    "historial": [],
    "ultimo_contexto": [],
    "ofertas": []
})

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

SYSTEM_PROMPT = """
Eres "Jobly", un asesor laboral de la Bolsa de trabajo PUCP virtual amigable, proactivo y muy servicial. Tu objetivo principal es ayudar a los usuarios a encontrar ofertas de empleo que se ajusten a su perfil, utilizando EXCLUSIVAMENTE la información de las ofertas de trabajo que se te proporcionan en el contexto.

Tu personalidad:
- Amable y cercano: Usa un tono conversacional y empático. Tutea al usuario.
- Profesional y preciso: Basa TODAS tus respuestas en los datos proporcionados. NUNCA inventes información, sueldos, requisitos o detalles que no estén en el contexto. Si no tienes la información, di amablemente que no la encuentras en la oferta.
- Orientador: No te limites a listar empleos. Anima al usuario, resalta los puntos clave de una oferta y guíalo en su búsqueda.

Cómo debes actuar:
1.  Al iniciar una conversación o una nueva búsqueda, saluda cordialmente y presenta los resultados de forma clara y resumida. Puedes usar listas o viñetas con emojis para que sea más legible, de se preferente tambien pidele su nombre y recuerdalo.
2.  Si el usuario hace una pregunta de seguimiento sobre una oferta que ya mencionaste (ej: "dame más detalles de la primera"), usa el contexto que ya tienes para responder en detalle sobre esa oferta específica.
3.  Si la información solicitada (ej: "email de contacto") no está en la descripción de la oferta, indícalo claramente. Ejemplo: "En los detalles de esta oferta no se especifica un email de contacto, pero puedes postular a través de su web".
4.  Si no encuentras ninguna oferta que coincida con la búsqueda, sé honesto y ofrécete a intentar con otros términos. Ejemplo: "Hola, de momento no he encontrado ofertas para 'físico nuclear'. ¿Te gustaría que buscara por otro puesto o habilidad?".
5.  Mantén las respuestas concisas y adaptadas para WhatsApp, pero sin perder la calidez.
"""

# ===================== FUNCIONES AUXILIARES =====================
def cargar_empleos():
    with open("jobs_for_chatbot.json", "r", encoding="utf-8") as f:
        return json.load(f)

def safe_join_lista(lista, separador=", "):
    if not lista:
        return "No especificado"
    elementos_limpios = [str(item) for item in lista if item and str(item).strip()]
    return separador.join(elementos_limpios) if elementos_limpios else "No especificado"

def crear_documento_empleo(empleo):
    contenido = f"""
Título: {empleo.get('title', 'Sin título')}
Empresa: {empleo.get('company', 'Sin empresa')}
Ubicación: {empleo.get('location', 'Sin ubicación')}
Tipo: {empleo.get('job_type', 'Sin especificar')}
Salario: {empleo.get('salary_info', 'No especificado')}
Descripción: {empleo.get('description', 'Sin descripción')}
Requisitos: {empleo.get('requirements', 'Sin requisitos')}
Email: {empleo.get('contact_email', 'No especificado')}
Modalidad: {empleo.get('remote_type', 'No especificado')}
Experiencia: {empleo.get('experience_level', 'No especificado')}
Educación: {empleo.get('education_level', 'No especificado')}
Carreras: {safe_join_lista(empleo.get('majors', []))}
Idiomas: {safe_join_lista(empleo.get('languages', []))}
Vacantes: {empleo.get('vacancies', 'No especificado')}
"""
    return Document(page_content=contenido.strip(), metadata=empleo)

def crear_y_guardar_vectorstore():
    print("🛠 Creando base vectorial...")
    empleos = cargar_empleos()
    documentos = [crear_documento_empleo(e) for e in empleos]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documentos)
    os.makedirs(VECTORSTORE_PATH, exist_ok=True)
    vectorstore = Chroma.from_documents(chunks, embedding=embedding_model, persist_directory=VECTORSTORE_PATH)
    vectorstore.persist()
    print(f"✅ Vectorstore creado con {len(chunks)} chunks.")
    return vectorstore

def cargar_vectorstore():
    if not os.path.exists(VECTORSTORE_PATH) or not os.listdir(VECTORSTORE_PATH):
        return crear_y_guardar_vectorstore()
    vectorstore = Chroma(persist_directory=VECTORSTORE_PATH, embedding_function=embedding_model)
    return vectorstore

def generar_con_groq(mensajes: list, modelo: str = "llama3-8b-8192") -> str:
    try:
        response = client.chat.completions.create(
            model=modelo,
            messages=mensajes,
            temperature=0.5,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"🚨 Error Groq: {e}")
        return "Lo siento, tengo problemas para responder ahora. Intenta de nuevo."

def es_pregunta_de_seguimiento(texto: str):
    texto = texto.lower().strip()
    claves = ["detalle", "más info", "más detalles", "dime más", "oferta", "primera", "segunda", "tercera"]
    return any(p in texto for p in claves)

def extraer_numero_oferta(texto: str):
    for palabra in texto.split():
        if palabra.isdigit():
            return int(palabra)
    return None

# ===================== CARGA VECTORSTORE =====================
vectorstore = cargar_vectorstore()

# ===================== API FASTAPI =====================
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"mensaje": "Jobly está en línea ✅"}

@app.post("/twilio", response_class=PlainTextResponse)
async def recibir_whatsapp(Body: str = Form(...), From: str = Form(...)):
    user_id = From
    pregunta_usuario = Body.strip()
    estado = conversaciones[user_id]
    historial = estado["historial"]

    contexto_texto = ""
    if historial and es_pregunta_de_seguimiento(pregunta_usuario):
        num = extraer_numero_oferta(pregunta_usuario)
        if num and num <= len(estado["ofertas"]):
            oferta = estado["ofertas"][num-1]
            contexto_texto = f"[Oferta {num}]\n{oferta['contenido']}"
        else:
            contexto_texto = "\n\n".join([f"[Oferta {i+1}]\n{o['contenido']}" for i,o in enumerate(estado["ofertas"])])
    else:
        docs = vectorstore.similarity_search(pregunta_usuario, k=3)
        estado["ultimo_contexto"] = docs
        estado["ofertas"] = [{"id": i+1, "contenido": doc.page_content} for i, doc in enumerate(docs)]
        contexto_texto = "\n\n".join([f"[Oferta {i+1}]\n{doc.page_content}" for i, doc in enumerate(docs)])

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turno in historial[-2:]:
        mensajes.append({"role": "user", "content": turno["usuario"]})
        mensajes.append({"role": "assistant", "content": turno["bot"]})

    prompt_usuario = f"""
Aquí están las ofertas disponibles (usa solo esto):
{contexto_texto}

Pregunta: "{pregunta_usuario}"
"""
    mensajes.append({"role": "user", "content": prompt_usuario})
    respuesta_bot = generar_con_groq(mensajes)

    historial.append({"usuario": pregunta_usuario, "bot": respuesta_bot})
    estado["historial"] = historial[-5:]

    twilio_resp = MessagingResponse()
    twilio_resp.message(respuesta_bot)
    return PlainTextResponse(twilio_resp.to_xml(), media_type="application/xml")

if __name__ == "__main__":
    print("🚀 Jobly corriendo en http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
