// Configuración de la aplicación
export const config = {
  // URL del backend - cambiar según el entorno
  BACKEND_URL: 'http://localhost:5000',
  
  // Modo de desarrollo - usar datos de prueba
  USE_MOCK_DATA: true, // Cambiar a false cuando tengas el backend funcionando
  
  // Configuración del chat
  CHAT_CONFIG: {
    welcomeMessage: '¡Hola! Soy Jobly, tu asistente para encontrar empleos. Escribe qué tipo de trabajo estás buscando y te ayudaré a encontrar las mejores oportunidades.',
    loadingMessage: 'Buscando empleos...',
    errorMessage: 'Lo siento, hubo un error al buscar empleos. Por favor, intenta de nuevo.'
  },
  
  // Configuración de la interfaz
  UI_CONFIG: {
    maxMessageLength: 500,
    animationDuration: 300,
    autoScrollDelay: 100
  }
};

export default config;
