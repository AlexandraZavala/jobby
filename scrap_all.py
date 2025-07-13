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

driver.quit()
