# 🚀 Guía de Inicio Rápido - Jobly Frontend

## ¿Qué es Jobly?

Jobly es un chatbot inteligente que ayuda a los usuarios a encontrar ofertas de trabajo mediante consultas en lenguaje natural. Los usuarios pueden escribir cosas como "quiero un trabajo de practicante en análisis de datos" y el sistema les mostrará ofertas relevantes.

## 🏗️ Estructura del Proyecto

```
src/
├── components/           # Componentes reutilizables
│   ├── ChatBox.jsx      # 💬 Componente principal del chat
│   ├── JobCard.jsx      # 💼 Tarjeta para mostrar empleos
│   ├── LoadingSpinner.jsx # ⏳ Indicador de carga
│   └── SuggestedQueries.jsx # 💡 Sugerencias de consultas
├── pages/               # Páginas de la aplicación
│   └── HomePage.jsx     # 🏠 Página principal
├── services/            # Servicios y API
│   └── api.js          # 🌐 Funciones para backend
├── config/              # Configuración
│   └── config.js       # ⚙️ Configuración global
└── assets/              # Recursos estáticos
```

## 🎯 Funcionalidades Implementadas

- ✅ **Chat en tiempo real**: Interfaz de conversación intuitiva
- ✅ **Búsqueda inteligente**: Procesamiento de consultas en lenguaje natural
- ✅ **Tarjetas de empleo**: Visualización atractiva de ofertas laborales
- ✅ **Historial de conversación**: Mantiene el contexto de la charla
- ✅ **Estado de carga**: Indicadores visuales mientras busca empleos
- ✅ **Sugerencias**: Consultas predefinidas para guiar al usuario
- ✅ **Responsive**: Funciona en móviles y desktop
- ✅ **Modo de prueba**: Datos mock para testing sin backend

## 🔧 Configuración

### Cambiar entre Modo de Prueba y Producción

Edita `src/config/config.js`:

```javascript
export const config = {
  // Cambiar a false cuando tengas el backend funcionando
  USE_MOCK_DATA: true, // true = datos de prueba, false = backend real
  
  // URL de tu backend
  BACKEND_URL: 'http://localhost:5000',
  
  // ... más configuraciones
};
```

### Configurar tu Backend

Tu backend debe tener un endpoint `POST /query_jobs` que:

**Reciba**:
```json
{
  "query": "quiero un trabajo de practicante en análisis de datos"
}
```

**Responda**:
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

## 🎨 Personalización

### Cambiar Colores
Edita las variables CSS en los archivos `.css` de cada componente.

### Modificar Mensajes
Edita `src/config/config.js`:
```javascript
CHAT_CONFIG: {
  welcomeMessage: 'Tu mensaje personalizado aquí...',
  loadingMessage: 'Mensaje de carga personalizado...',
  errorMessage: 'Mensaje de error personalizado...'
}
```

### Agregar Nuevas Consultas Sugeridas
Edita `src/components/SuggestedQueries.jsx` y modifica el array `suggestedQueries`.

## 🛠️ Comandos Útiles

```bash
# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev

# Construir para producción
npm run build

# Preview de producción
npm run preview

# Linting
npm run lint
```

## 🐛 Troubleshooting

### El servidor no inicia
- Verifica que tienes Node.js instalado
- Ejecuta `npm install` para instalar dependencias

### No se muestran empleos
- Verifica que `USE_MOCK_DATA: true` en `config.js`
- Revisa la consola del navegador para errores

### Problemas de conexión al backend
- Verifica que la URL en `BACKEND_URL` sea correcta
- Asegúrate de que el backend esté ejecutándose
- Revisa las políticas CORS del backend

## 📱 URLs Importantes

- **Desarrollo**: http://localhost:5174 (o el puerto que muestre Vite)
- **Backend esperado**: http://localhost:5000

## 🚀 Próximos Pasos

1. **Configura tu backend**: Implementa el endpoint `/query_jobs`
2. **Cambia a modo producción**: `USE_MOCK_DATA: false`
3. **Personaliza el diseño**: Ajusta colores y estilos
4. **Añade funcionalidades**: Filtros, guardado de empleos, etc.

¡Tu chatbot Jobly está listo para encontrar empleos! 🎉
