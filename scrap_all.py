from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import os
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales desde variables de entorno
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

if not EMAIL or not PASSWORD:
    print("❌ Error: Las variables EMAIL y PASSWORD deben estar definidas en el archivo .env")
    exit(1)

# --- Configuración del navegador en modo headless ---
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Modo headless
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--disable-plugins")
options.add_argument("--disable-images")
options.add_argument("--window-size=1920,1080")  # Tamaño de ventana fijo
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# --- Inyectar interceptor de XHR para capturar los empleos listados ---
xhr_interceptor = """
(function() {
  const open = XMLHttpRequest.prototype.open;
  window._xhrResults = [];

  XMLHttpRequest.prototype.open = function(method, url) {
    this._url = url;
    return open.apply(this, arguments);
  };

  const send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function() {
    const _this = this;
    this.addEventListener("load", function() {
      try {
        if (_this._url.includes("/api/v2/jobs") && _this._url.includes("json_mode=read_only")) {
          const json = JSON.parse(_this.response);
          if (json.models && json.models.length > 0) {
            window._xhrResults.push(...json.models);
            console.log("📥 Capturados", json.models.length, "empleos.");
          } else {
            window._xhrResults.push("END_OF_PAGE");
          }
        }
      } catch (err) {
        console.warn("❌ Error al interceptar:", err);
      }
    });
    return send.apply(this, arguments);
  };
})();
"""
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": xhr_interceptor
})

# --- Función para verificar si ya estamos logueados ---
def verificar_login_status():
    try:
        # Verificar si ya estamos en la página de empleos
        if driver.find_element(By.CLASS_NAME, "list-page-job-search"):
            print("✅ Ya estamos logueados y en la página de empleos")
            return True
        return False
    except:
        return False

# --- Función para hacer login automático ---
def hacer_login():
    print("🔐 Iniciando login automático...")
    
    # Ir a la página de login
    driver.get("https://pucp-csm.symplicity.com/students/app/jobs/search")
    time.sleep(3)  # Esperar a que la página cargue completamente
    
    # Verificar si ya estamos logueados
    if verificar_login_status():
        return True
    
    try:
        # Esperar a que aparezca el formulario de login
        print("⏳ Esperando formulario de login...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        print("📝 Ingresando credenciales...")
        # Ingresar email
        email_field = driver.find_element(By.ID, "username")
        email_field.clear()
        email_field.send_keys(EMAIL)
        time.sleep(1)
        
        # Ingresar contraseña
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        time.sleep(1)
        
        # Buscar el botón de login con el selector correcto basado en el HTML real
        login_button = None
        selectors = [
            "//input[@type='submit' and @value='Iniciar sesión']",
            "//input[@type='submit']",
            "//button[@type='submit']",
            "//input[contains(@class, 'input-submit')]",
            "//input[contains(@class, 'btn_primary')]",
            "//button[contains(text(), 'Login')]",
            "//button[contains(text(), 'Iniciar')]",
            "//button[contains(text(), 'Sign')]"
        ]
        
        for selector in selectors:
            try:
                login_button = driver.find_element(By.XPATH, selector)
                print(f"✅ Botón de login encontrado con selector: {selector}")
                break
            except:
                continue
        
        if not login_button:
            # Si no encontramos el botón, intentar con Enter en el campo de contraseña
            print("⚠️ No se encontró botón de login, intentando con Enter...")
            password_field.send_keys(Keys.RETURN)
        else:
            login_button.click()
        
        print("⏳ Esperando redirección después del login...")
        time.sleep(3)  # Esperar a que se procese el login
        
        # Esperar a que se complete el login (verificar que estamos en la página de empleos)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "list-page-job-search"))
        )
        
        print("✅ Login exitoso")
        return True
        
    except TimeoutException as e:
        print(f"❌ Error en el login: Timeout - {e}")
        # Intentar verificar si ya estamos logueados
        if verificar_login_status():
            return True
        return False
    except Exception as e:
        print(f"❌ Error inesperado durante el login: {e}")
        return False

# --- Hacer login automático ---
if not hacer_login():
    driver.quit()
    exit(1)

print("🧭 Iniciando scraping navegando con clics en 'Siguiente'...")

page = 1
max_espera = 10

while True:
    print(f"\n📄 Página {page}")

    # Scroll para activar carga de empleos
    try:
        scroll_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "list-page-job-search"))
        )
        for _ in range(5):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_area)
            time.sleep(0.3)
    except TimeoutException:
        print("❌ No se pudo hacer scroll. Terminando.")
        break

    prev_count = driver.execute_script("return window._xhrResults.length")

    # Clic en botón "Siguiente"
    try:
        btn_siguiente = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button[span[text()='Siguiente']]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", btn_siguiente)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn_siguiente)
        print(f"✅ Clic en 'Siguiente' hecho (página {page})")
    except TimeoutException:
        print("✅ No se encontró botón 'Siguiente'. Fin del scraping.")
        break
    except JavascriptException as e:
        print("❌ Falló el clic con JS:", e)
        break

    for _ in range(max_espera * 2):
        time.sleep(0.5)
        new_count = driver.execute_script("return window._xhrResults.length")
        if new_count > prev_count:
            break

    if new_count == prev_count:
        print("⚠️ No se cargaron nuevos empleos tras hacer clic. Deteniendo.")
        break

    page += 1

# --- Guardar resultados de empleos listados ---
resultados = driver.execute_script("return window._xhrResults.filter(x => typeof x === 'object')")
print(f"\n📦 Total empleos recolectados: {len(resultados)}")
with open("jobs_raw.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)
print("✅ Empleos guardados en 'jobs_raw.json'")

# --- Paso 2: Extraer detalles individuales de cada empleo ---
print(f"\n🔎 Procesando {len(resultados)} empleos para extraer detalles...")

driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])

detalles = []
fallidos = []

for idx, job in enumerate(resultados, 1):
    job_id = job.get("job_id")
    if not job_id:
        print(f"⚠️ ({idx}) Empleo sin 'job_id': {job.get('job_title', 'Sin título')}")
        continue

    url = f"https://pucp-csm.symplicity.com/api/v3/jobs/{job_id}"

    try:
        driver.get(url)
        driver.implicitly_wait(3)

        pre = driver.find_elements("tag name", "pre")
        if not pre:
            print(f"⚠️ ({idx}) No se encontró JSON visible en: {url}")
            fallidos.append(job_id)
            continue

        raw_text = pre[0].text.strip()
        job_detail = json.loads(raw_text)
        detalles.append(job_detail)

        print(f"✅ ({idx}) Detalle extraído para ID {job_id}")

    except Exception as e:
        print(f"❌ ({idx}) Error con ID {job_id}: {e}")
        fallidos.append(job_id)

# --- Guardar detalles ---
with open("detalles_empleos.json", "w", encoding="utf-8") as f:
    json.dump(detalles, f, ensure_ascii=False, indent=2)

print(f"\n📦 Detalles guardados: {len(detalles)} empleos en 'detalles_empleos.json'")

if fallidos:
    print(f"⚠️ Fallaron {len(fallidos)} empleos: {fallidos}")

# --- Guardar detalles formateados para chatbot ---
print(f"\n🔎 Formateando {len(detalles)} empleos para chatbot...")

# Importar las funciones de formateo
import re

def clean_html_tags(text):
    """Limpia las etiquetas HTML del texto"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&middot;', '•')
    text = text.replace('&oacute;', 'ó')
    text = text.replace('&aacute;', 'á')
    text = text.replace('&eacute;', 'é')
    text = text.replace('&iacute;', 'í')
    text = text.replace('&uacute;', 'ú')
    text = text.replace('&ntilde;', 'ñ')
    text = text.replace('&nbsp;', ' ')
    return text.strip()


def format_job_for_chatbot(job_data):
    """Formatea un empleo para el chatbot"""
    job_info = {
        "id": job_data.get("job_id", ""),
        "visual_id": job_data.get("visual_id", ""),
        "title": clean_html_tags(job_data.get("job_title", "")).strip(),
        "company": job_data.get("employer_name", ""),
        "location": "",
        "job_type": "",
        "salary_info": "",
        "start_date": "",
        "end_date": "",
        "description": "",
        "requirements": "",
        "contact_email": "",
        "remote_type": "",
        "experience_level": "",
        "education_level": "",
        "majors": [],
        "languages": [],
        "vacancies": "",
        "hours_per_week": ""
    }
    
    # Ubicación
    if job_data.get("location"):
        job_info["location"] = ", ".join([loc.get("_label", "") for loc in job_data["location"] if loc.get("_label")])
    
    # Tipo de empleo
    if job_data.get("job_type"):
        job_info["job_type"] = ", ".join([jt.get("_label", "") for jt in job_data["job_type"] if jt.get("_label")])
    
    # Información de salario
    if job_data.get("compensation_from") or job_data.get("compensation_to"):
        from_salary = job_data.get("compensation_from", "")
        to_salary = job_data.get("compensation_to", "")
        frequency = job_data.get("compensation_frequency", {}).get("_label", "")
        
        if from_salary and to_salary:
            job_info["salary_info"] = f"{from_salary} - {to_salary} {frequency}"
        elif from_salary:
            job_info["salary_info"] = f"Desde {from_salary} {frequency}"
        elif to_salary:
            job_info["salary_info"] = f"Hasta {to_salary} {frequency}"
    
    # Fechas
    if job_data.get("job_start"):
        job_info["start_date"] = job_data["job_start"]
    if job_data.get("job_end"):
        job_info["end_date"] = job_data["job_end"]
    
    # Descripción
    job_info["description"] = clean_html_tags(job_data.get("job_desc", ""))
    
    # Requisitos
    job_info["requirements"] = clean_html_tags(job_data.get("qualifications", ""))
    
    
    # Email de contacto
    job_info["contact_email"] = job_data.get("resume_email", "")
    
    # Tipo de trabajo remoto
    if job_data.get("symp_remote_onsite"):
        job_info["remote_type"] = job_data["symp_remote_onsite"].get("_label", "")
    
    # Nivel de experiencia
    if job_data.get("custom_field_6"):
        job_info["experience_level"] = job_data["custom_field_6"].get("_label", "")
    
    # Nivel de educación
    if job_data.get("degree_level"):
        job_info["education_level"] = ", ".join([dl.get("_label", "") for dl in job_data["degree_level"] if dl.get("_label")])
    
    # Carreras requeridas
    if job_data.get("major"):
        job_info["majors"] = [m.get("_label", "") for m in job_data["major"] if m.get("_label")]
    
    # Idiomas
    if job_data.get("custom_field_1"):
        job_info["languages"] = [job_data["custom_field_1"].get("_label", "")]
    
    # Número de vacantes
    if job_data.get("nmero_de_vacantes_2"):
        job_info["vacancies"] = job_data["nmero_de_vacantes_2"].get("_label", "")
    
    # Horas por semana
    if job_data.get("custom_field_10"):
        job_info["hours_per_week"] = job_data["custom_field_10"].get("_label", "")
    
    return job_info

def create_searchable_text(job_info):
    """Crea un texto searchable para el chatbot"""
    searchable_parts = [
        job_info["title"],
        job_info["company"],
        job_info["location"],
        job_info["job_type"],
        job_info["description"],
        job_info["requirements"],
        " ".join([str(m) for m in job_info["majors"] if m]) if job_info["majors"] else "",
        job_info["experience_level"],
        job_info["education_level"],
        " ".join([str(l) for l in job_info["languages"] if l]) if job_info["languages"] else "",
        job_info["remote_type"]
    ]
    
    return " ".join([part for part in searchable_parts if part])

# Formatear todos los empleos
formatted_jobs = []
for i, job in enumerate(detalles, 1):
    try:
        formatted_job = format_job_for_chatbot(job)
        formatted_job["searchable_text"] = create_searchable_text(formatted_job)
        formatted_jobs.append(formatted_job)
        
        if i % 10 == 0:
            print(f"✅ Formateados {i}/{len(detalles)} empleos")
            
    except Exception as e:
        print(f"⚠️ Error formateando empleo {i}: {e}")
        continue

# Guardar empleos formateados
with open("jobs_for_chatbot.json", "w", encoding="utf-8") as f:
    json.dump(formatted_jobs, f, ensure_ascii=False, indent=2)

print(f"\n✅ Formateo completado!")
print(f"📦 Empleos formateados guardados en 'jobs_for_chatbot.json'")
print(f"📊 Total de empleos formateados: {len(formatted_jobs)}")


driver.quit()
