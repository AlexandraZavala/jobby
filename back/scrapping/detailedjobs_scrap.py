from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

# Configuración
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--disable-plugins")
options.add_argument("--disable-images")
options.add_argument("--incognito")  # Modo incógnito para evitar perfiles
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Inicia navegador
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Abrir primera pestaña solo para login
driver.get("https://pucp-csm.symplicity.com/students/app/jobs/search")
input("🔐 Inicia sesión completamente en la web, luego presiona ENTER aquí para continuar...")

# Cargar IDs de trabajos
with open("jobs_raw.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

print(f"🔎 Procesando {len(jobs)} empleos para extraer detalles...\n")

# Abre nueva pestaña para recolectar los JSON de detalle
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[1])

detalles = []
fallidos = []

for idx, job in enumerate(jobs, 1):
    job_id = job.get("job_id")  # USAMOS 'job_id' porque ese es el correcto
    if not job_id:
        print(f"⚠️ ({idx}) Empleo sin 'job_id': {job.get('job_title', 'Sin título')}")
        continue

    url = f"https://pucp-csm.symplicity.com/api/v3/jobs/{job_id}"

    try:
        driver.get(url)
        driver.implicitly_wait(3)

        # Espera directa por etiqueta <pre> (donde está el JSON visible)
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

# Guardar resultados
with open("detalles_empleos.json", "w", encoding="utf-8") as f:
    json.dump(detalles, f, ensure_ascii=False, indent=2)

print(f"\n📦 Detalles guardados: {len(detalles)} empleos en 'detalles_empleos.json'")

if fallidos:
    print(f"⚠️ Fallaron {len(fallidos)} empleos: {fallidos}")

driver.quit()
