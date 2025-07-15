# Jobly - Frontend

Jobly es un chatbot inteligente que ayuda a los usuarios a encontrar ofertas de trabajo según sus consultas en lenguaje natural.

## Características

- **Interfaz de chat intuitiva**: Los usuarios pueden escribir consultas como "quiero un trabajo de practicante en análisis de datos"
- **Búsqueda inteligente**: Utiliza procesamiento de lenguaje natural para encontrar empleos relevantes
- **Respuestas visuales**: Las ofertas de trabajo se muestran como tarjetas atractivas con información detallada
- **Historial de conversación**: Mantiene un registro de todas las interacciones del usuario
- **Diseño responsivo**: Funciona perfectamente en dispositivos móviles y de escritorio

## Tecnologías Utilizadas

- **React 19**: Biblioteca de JavaScript para construir interfaces de usuario
- **Vite**: Herramienta de construcción y desarrollo rápido
- **Axios**: Cliente HTTP para realizar llamadas al backend
- **CSS3**: Estilos modernos con gradientes y animaciones

## Estructura del Proyecto

```
src/
├── components/
│   ├── ChatBox.jsx          # Componente principal del chat
│   ├── ChatBox.css
│   ├── JobCard.jsx          # Tarjeta para mostrar ofertas de trabajo
│   ├── JobCard.css
│   ├── LoadingSpinner.jsx   # Indicador de carga
│   └── LoadingSpinner.css
├── pages/
│   ├── HomePage.jsx         # Página principal
│   └── HomePage.css
├── services/
│   └── api.js              # Funciones para comunicación con el backend
├── App.jsx
├── App.css
├── index.css
└── main.jsx
```

## Instalación y Uso

1. **Instalar dependencias**:
   ```bash
   npm install
   ```

2. **Ejecutar en modo desarrollo**:
   ```bash
   npm run dev
   ```

3. **Configurar backend**: 
   - El frontend está configurado para conectarse a `http://localhost:5000`
   - Edita `src/services/api.js` para cambiar la URL del backend
   - Por defecto usa `mockQueryJobs` para testing sin backend

4. **Construcción para producción**:
   ```bash
   npm run build
   ```

## API del Backend

El frontend espera un endpoint `POST /query_jobs` que:

**Request**:
```json
{
  "query": "quiero un trabajo de practicante en análisis de datos"
}
```

**Response**:
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Practicante en Análisis de Datos",
      "company": "Tech Solutions SAC",
      "location": "Lima, Perú",
      "description": "Descripción del trabajo..."
    }
  ],
  "message": "Encontré 3 ofertas relacionadas con tu búsqueda"
}
```

## Personalización

- **Colores**: Edita las variables CSS en `index.css` y los archivos de componentes
- **Backend URL**: Cambia `BASE_URL` en `src/services/api.js`
- **Modo de prueba**: Usa `mockQueryJobs` en lugar de `queryJobs` para testing sin backend

## Contribución

1. Fork el proyecto
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request
