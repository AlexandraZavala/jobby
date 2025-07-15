import React from 'react';
import './JobCard.css';

const JobCard = ({ job }) => {
  return (
    <div className="job-card">
      <div className="job-header">
        <h3 className="job-title">{job.title}</h3>
        <span className="job-company">{job.company}</span>
      </div>
      <div className="job-location">
        <span className="location-icon">📍</span>
        {job.location}
      </div>
      <div className="job-description">
        {job.description}
      </div>
      <div className="job-actions">
        <button className="apply-btn">Ver detalles</button>
      </div>
    </div>
  );
};

export default JobCard;
