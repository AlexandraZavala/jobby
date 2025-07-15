import axios from 'axios';
import config from '../config/config.js';

// URL base del backend
const BASE_URL = config.BACKEND_URL;

// Función para hacer la consulta de empleos
export const queryJobs = async (queryText) => {
  try {
    const response = await axios.post(`${BASE_URL}/query_jobs`, {
      query: queryText
    }, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error al consultar empleos:', error);
    throw new Error(config.CHAT_CONFIG.errorMessage);
  }
};

// Función para simular la respuesta del backend (para testing)
export const mockQueryJobs = async (queryText) => {
  // Simula delay de red
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Diferentes respuestas según la consulta
  const mockResponses = {
    'análisis de datos': [
      {
        id: 1,
        title: "Practicante en Análisis de Datos",
        company: "Tech Solutions SAC",
        location: "Lima, Perú",
        description: "Buscamos un practicante entusiasta para unirse a nuestro equipo de análisis de datos. Trabajarás con Python, SQL y herramientas de visualización."
      },
      {
        id: 2,
        title: "Analista de Datos Junior",
        company: "DataCorp",
        location: "San Isidro, Lima",
        description: "Oportunidad para desarrollar habilidades en análisis de datos utilizando Excel, Power BI y Python. Ideal para recién graduados."
      }
    ],
    'desarrollador': [
      {
        id: 3,
        title: "Desarrollador Frontend React",
        company: "WebTech Solutions",
        location: "Surco, Lima",
        description: "Únete a nuestro equipo como desarrollador Frontend. Trabajarás con React, TypeScript y tecnologías modernas."
      },
      {
        id: 4,
        title: "Desarrollador Full Stack",
        company: "CodeCraft",
        location: "Miraflores, Lima",
        description: "Buscamos desarrollador Full Stack con experiencia en JavaScript, Node.js y bases de datos."
      }
    ],
    'marketing': [
      {
        id: 5,
        title: "Especialista en Marketing Digital",
        company: "Digital Agency Pro",
        location: "Barranco, Lima",
        description: "Oportunidad para especialista en marketing digital con experiencia en SEO, SEM y redes sociales."
      }
    ]
  };

  // Buscar palabras clave en la consulta
  const normalizedQuery = queryText.toLowerCase();
  let selectedJobs = [];
  
  for (const [key, jobs] of Object.entries(mockResponses)) {
    if (normalizedQuery.includes(key)) {
      selectedJobs = jobs;
      break;
    }
  }
  
  // Si no encuentra coincidencias específicas, devolver trabajos de análisis de datos
  if (selectedJobs.length === 0) {
    selectedJobs = mockResponses['análisis de datos'];
  }
  
  return {
    jobs: selectedJobs,
    message: `Encontré ${selectedJobs.length} ofertas relacionadas con "${queryText}"`
  };
};

// Función para usar el chatbot inteligente con Together.ai
export const chatWithBot = async (mensaje) => {
  try {
    const response = await axios.post(`${BASE_URL}/chat`, {
      mensaje: mensaje
    }, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    return {
      respuesta: response.data.respuesta,
      empleos: response.data.empleos || null,
      success: true
    };
  } catch (error) {
    console.error('Error al chatear con el bot:', error);
    return {
      respuesta: "Lo siento, hubo un error al procesar tu consulta. Por favor, intenta de nuevo.",
      success: false
    };
  }
};

// Función principal que decide si usar datos reales o mock
export const searchJobs = async (queryText) => {
  if (config.USE_MOCK_DATA) {
    return await mockQueryJobs(queryText);
  } else {
    return await queryJobs(queryText);
  }
};

// Función para obtener detalles completos de un empleo específico
export const getJobDetails = async (jobId) => {
  try {
    const response = await axios.get(`${BASE_URL}/job/${jobId}`);
    
    if (response.data.found) {
      return {
        job: response.data.job,
        success: true
      };
    } else {
      return {
        job: null,
        success: false,
        error: 'Empleo no encontrado'
      };
    }
  } catch (error) {
    console.error('Error al obtener detalles del empleo:', error);
    return {
      job: null,
      success: false,
      error: 'Error al conectar con el servidor'
    };
  }
};
