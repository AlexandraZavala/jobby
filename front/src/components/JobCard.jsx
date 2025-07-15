import React, { useState } from 'react';
import JobDetailModal from './JobDetailModal';
import './JobCard.css';

const JobCard = ({ job }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Truncar descripción a las primeras 100 caracteres
  const truncateDescription = (text, maxLength = 100) => {
    if (!text) return 'Sin descripción disponible';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const handleViewDetails = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <>
      <div className="job-card">
        <div className="job-header">
          <h3 className="job-title">{job.title || 'Sin título'}</h3>
          <span className="job-company">{job.company || 'Sin empresa'}</span>
        </div>
        <div className="job-description">
          {truncateDescription(job.description)}
        </div>
        <div className="job-actions">
          <button className="apply-btn" onClick={handleViewDetails}>
            Ver detalles
          </button>
        </div>
      </div>

      <JobDetailModal
        jobId={job.id || job.visual_id}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </>
  );
};

export default JobCard;
