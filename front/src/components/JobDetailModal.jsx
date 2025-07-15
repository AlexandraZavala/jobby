import React, { useState, useEffect } from 'react';
import { getJobDetails } from '../services/api';
import './JobDetailModal.css';

const JobDetailModal = ({ jobId, isOpen, onClose }) => {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && jobId) {
      loadJobDetails();
    }
  }, [isOpen, jobId]);

  const loadJobDetails = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getJobDetails(jobId);
      
      if (response.success) {
        setJob(response.job);
      } else {
        setError(response.error || 'No se pudieron cargar los detalles del empleo');
      }
    } catch (err) {
      setError('Error al cargar los detalles del empleo');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const formatDate = (dateString) => {
    if (!dateString) return 'No especificado';
    try {
      return new Date(dateString).toLocaleDateString('es-PE', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const formatList = (items) => {
    if (!items || !Array.isArray(items)) return 'No especificado';
    if (items.length === 0) return 'No especificado';
    return items.join(', ');
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">
            {loading ? 'Cargando...' : job?.title || 'Detalles del empleo'}
          </h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Cargando detalles del empleo...</p>
            </div>
          )}

          {error && (
            <div className="error-container">
              <p className="error-message">❌ {error}</p>
              <button className="retry-button" onClick={loadJobDetails}>
                Reintentar
              </button>
            </div>
          )}

          {job && !loading && !error && (
            <>
              <div className="job-detail-section">
                <div className="company-info">
                  <h3>🏢 {job.company || 'Sin empresa'}</h3>
                  <div className="job-meta">
                    <span className="meta-item">📍 {job.location || 'Sin ubicación'}</span>
                    <span className="meta-item">💼 {job.job_type || 'No especificado'}</span>
                    <span className="meta-item">🌐 {job.remote_type || 'No especificado'}</span>
                  </div>
                </div>
              </div>

              <div className="job-detail-section">
                <h4>📋 Descripción del puesto</h4>
                <p className="job-full-description">
                  {job.description || 'Sin descripción disponible'}
                </p>
              </div>

              {job.requirements && (
                <div className="job-detail-section">
                  <h4>✅ Requisitos</h4>
                  <div className="requirements-text">
                    {job.requirements.split('\n').map((req, index) => (
                      req.trim() && <p key={index} className="requirement-item">{req.trim()}</p>
                    ))}
                  </div>
                </div>
              )}

              <div className="job-detail-section">
                <h4>🎯 Información del puesto</h4>
                <div className="job-info-grid">
                  <div className="info-item">
                    <span className="info-label">Nivel de experiencia:</span>
                    <span className="info-value">{job.experience_level || 'No especificado'}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Nivel educativo:</span>
                    <span className="info-value">{job.education_level || 'No especificado'}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Salario:</span>
                    <span className="info-value">{job.salary_info || 'No especificado'}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Fecha de inicio:</span>
                    <span className="info-value">{formatDate(job.start_date)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Fecha límite:</span>
                    <span className="info-value">{formatDate(job.end_date)}</span>
                  </div>
                </div>
              </div>

              {job.majors && job.majors.length > 0 && (
                <div className="job-detail-section">
                  <h4>🎓 Carreras relacionadas</h4>
                  <div className="majors-list">
                    {job.majors.map((major, index) => (
                      <span key={index} className="major-tag">
                        {major.replace('PREGRADO/', '')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {job.contact_email && (
                <div className="job-detail-section">
                  <h4>📧 Contacto</h4>
                  <a href={`mailto:${job.contact_email}`} className="contact-email">
                    {job.contact_email}
                  </a>
                </div>
              )}
            </>
          )}
        </div>

        {job && !loading && !error && (
          <div className="modal-footer">
            <button className="close-button" onClick={onClose}>
              Cerrar
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobDetailModal;
