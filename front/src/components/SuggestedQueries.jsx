import React from 'react';
import './SuggestedQueries.css';

const SuggestedQueries = ({ onQuerySelect, isVisible }) => {
  const suggestedQueries = [
    "Quiero un trabajo de practicante en análisis de datos",
    "Busco empleo como desarrollador frontend con React",
    "Oportunidades en marketing digital",
    "Trabajo remoto en programación",
    "Puestos de data scientist junior",
    "Empleos en startups tecnológicas"
  ];

  if (!isVisible) return null;

  return (
    <div className="suggested-queries">
      <h4>💡 Prueba estas consultas:</h4>
      <div className="queries-grid">
        {suggestedQueries.map((query, index) => (
          <button
            key={index}
            className="query-suggestion"
            onClick={() => onQuerySelect(query)}
          >
            {query}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestedQueries;
