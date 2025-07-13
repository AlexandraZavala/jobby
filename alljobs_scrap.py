from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException
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

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Interceptor de XHR
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

# Abrir primera página manualmente
driver.get("https://pucp-csm.symplicity.com/students/app/jobs/search?perPage=20&page=1&sort=!postdate")
input("🔐 Inicia sesión completamente. Luego presiona ENTER aquí para continuar...")

print("🧭 Iniciando scraping navegando con clics en 'Siguiente'...")

page = 1
max_espera = 10

while True:
    print(f"\n📄 Página {page}")

    # Scroll a lista para que cargue todo
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

    # Verificar cuántos empleos hay hasta ahora
    prev_count = driver.execute_script("return window._xhrResults.length")

    # Buscar botón "Siguiente"
    try:
        btn_siguiente = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button[span[text()='Siguiente']]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", btn_siguiente)
        time.sleep(0.5)

        # Click real con JavaScript
        driver.execute_script("arguments[0].click();", btn_siguiente)
        print(f"✅ Clic en 'Siguiente' hecho (página {page})")
    except TimeoutException:
        print("✅ No se encontró botón 'Siguiente'. Fin del scraping.")
        break
    except JavascriptException as e:
        print("❌ Falló el clic con JS:", e)
        break

    # Esperar a que se carguen nuevos empleos
    for _ in range(max_espera * 2):
        time.sleep(0.5)
        new_count = driver.execute_script("return window._xhrResults.length")
        if new_count > prev_count:
            break

    if new_count == prev_count:
        print("⚠️ No se cargaron nuevos empleos tras hacer clic. Deteniendo.")
        break

    page += 1

# Guardar resultados
resultados = driver.execute_script("return window._xhrResults.filter(x => typeof x === 'object')")
print(f"\n📦 Total empleos recolectados: {len(resultados)}")
with open("jobs_raw.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

driver.quit()
print("✅ Empleos guardados en 'jobs_raw.json'")
