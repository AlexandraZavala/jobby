import json
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import subprocess
import sys

def ejecutar_scraping():
    """Ejecuta el script de scraping"""
    print("🚀 Iniciando scraping...")
    try:
        result = subprocess.run([sys.executable, "scrap_all.py"], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Scraping completado")
            return True
        else:
            print(f"❌ Error en scraping: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def cargar_empleos_formateados():
    """Carga los empleos ya formateados"""
    try:
        with open("jobs_for_chatbot.json", "r", encoding="utf-8") as f:
            empleos = json.load(f)
        print(f"📦 Cargados {len(empleos)} empleos")
        return empleos
    except FileNotFoundError:
        print("❌ No se encontró jobs_for_chatbot.json")
        return []
    except Exception as e:
        print(f"❌ Error cargando: {e}")
        return []

def procesar_empleos(hacer_scraping=True):
    """Procesa los empleos - puede hacer scraping o usar JSON existente"""
    if hacer_scraping:
        print("🔄 Haciendo scraping nuevo...")
        if not ejecutar_scraping():
            print("❌ Falló el scraping")
            return None
    else:
        print("📁 Usando JSON existente")
    
    empleos = cargar_empleos_formateados()
    if not empleos:
        print("❌ No se pudieron cargar empleos")
        return None
    
    return empleos

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

def dividir_documentos(empleos):
    """Divide los empleos en documentos individuales"""
    print("�� Creando documentos...")
    
    documentos = []
    for i, empleo in enumerate(empleos, 1):
        try:
            doc = crear_documento_empleo(empleo)
            documentos.append(doc)
        except Exception as e:
            print(f"⚠️ Error documento {i}: {e}")
            continue
    
    print(f"📚 Creados {len(documentos)} documentos")
    return documentos

def crear_vectorstore(documentos):
    """Crea el vectorstore con Chroma usando HuggingFace embeddings"""
    print("🔍 Creando vectorstore...")
    
    try:
        print("🤖 Cargando modelo...")
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        documentos_divididos = text_splitter.split_documents(documentos)
        print(f"📊 Divididos en {len(documentos_divididos)} chunks")
        
        vectorstore = Chroma.from_documents(
            documents=documentos_divididos,
            embedding=embeddings_model,
            persist_directory="./chroma_db"
        )
        
        vectorstore.persist()
        print("✅ Vectorstore creado")
        return vectorstore
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def probar_retriever():
    """Prueba el retriever con consultas de ejemplo"""
    print("🧪 Probando retriever...")
    
    try:
        print("📂 Cargando vectorstore...")
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings_model
        )
        
        consultas_prueba = [
            "quiero un trabajo de practicante como desarrollador",
            "quiero un trabajo de practicante como desarrollador de software",
            "quiero un trabajo de practicante como desarrollador de software en lima",
            "quiero un trabajo de practicante profesional como analista de datos",
        ]
        
        print(f"🔍 Probando {len(consultas_prueba)} consultas...")
        
        for i, consulta in enumerate(consultas_prueba, 1):
            print(f"\n📝 '{consulta}'")
            
            resultados = vectorstore.similarity_search(consulta, k=3)
            
            if resultados:
                print(f"   ✅ {len(resultados)} resultados:")
                for j, doc in enumerate(resultados, 1):
                    metadatos = doc.metadata
                    titulo = metadatos.get('title', 'Sin título')
                    empresa = metadatos.get('company', 'Sin empresa')
                    ubicacion = metadatos.get('location', 'Sin ubicación')
                    
                    print(f"   {j}. {titulo} - {empresa} ({ubicacion})")
            else:
                print("   ❌ Sin resultados")
        
        print("✅ Prueba completada")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main(hacer_scraping=True, crear_vectorstore_bd=True):
    """Función principal con opción de scraping, creación de vectorstore y prueba"""
    print("🎯 Iniciando procesamiento...")
    
    empleos = procesar_empleos(hacer_scraping)
    if not empleos:
        return
    
    documentos = dividir_documentos(empleos)
    if not documentos:
        print("❌ No se pudieron crear documentos")
        return
    
    if crear_vectorstore_bd:
        vectorstore = crear_vectorstore(documentos)
        if not vectorstore:
            print("❌ No se pudo crear vectorstore")
            return
    
    probar_retriever()
    
    print("✅ Procesamiento completado")
    print(f"📊 {len(empleos)} empleos procesados")
    print(f"📚 {len(documentos)} documentos creados")


if __name__ == "__main__":
   
    HACER_SCRAPING = False  # True = hacer scraping, False = usar JSON existente
    CREAR_VECTORSTORE = False  # True = crear vectorstore, False = solo procesar documentos
   
    main(hacer_scraping=HACER_SCRAPING, crear_vectorstore_bd=CREAR_VECTORSTORE) 