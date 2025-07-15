from flask import Flask, request, jsonify
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv
from flask_cors import CORS
import google.generativeai as genai


load_dotenv()

app = Flask(__name__)
CORS(app)  #habilita CORS para cualquier origen (modo dev)

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

for m in genai.list_models():
    print(m.name, "→", m.supported_generation_methods)

    
# model = genai.GenerativeModel("models/gemini-1.5-pro")
model = genai.GenerativeModel("models/gemini-2.5-flash")

# Configurar embeddings y vectorstore
embedding_model = HuggingFaceEmbeddings(
    model_name="intfloat/e5-small-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_model
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "Pregunta vacía"}), 400

        # Recuperar contexto relevante
        docs = retriever.get_relevant_documents(question)
        context = "\n\n".join([doc.page_content for doc in docs])

        # Armar prompt para Gemini
        # prompt = f"""
        # # A continuación tienes información útil extraída de empleos:

        # # {context}

        # # Basado en esa información, responde a la siguiente pregunta:
        # # {question}
        # # """

        prompt = f"""
        Responde en formato Markdown detallado. Aquí tienes empleos disponibles:

        {context}

        Pregunta del usuario:
        {question}

        Si hay múltiples resultados, menciona hasta 3 con título, empresa y tipo de empleo.
        """

        response = model.generate_content(prompt)
        answer = response.text.strip()

        sources = [
            {
                "title": doc.metadata.get("title"),
                "company": doc.metadata.get("company"),
                "location": doc.metadata.get("location"),
                "id": doc.metadata.get("id"),
                "description": doc.page_content[:200]  # Primeros 200 caracteres del contenido
            }
            for doc in docs
        ]

        return jsonify({"answer": answer, "sources": sources})

    except Exception as e:
        print(f"❌ ERROR en /api/chat: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
