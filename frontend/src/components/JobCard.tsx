/**
 * Job card component — displays a job listing summary.
 */

import React from 'react'
import { MapPin, Clock, DollarSign, ExternalLink } from 'lucide-react'
import { Job } from '../api/endpoints'
import { useNavigate } from 'react-router-dom'

interface Props {
    job: Job
    score?: number
}

const JobCard: React.FC<Props> = ({ job, score }) => {
    const navigate = useNavigate()

    const timeAgo = (dateStr: string) => {
        const diff = Date.now() - new Date(dateStr).getTime()
        const days = Math.floor(diff / 86400000)
        if (days === 0) return 'Today'
        if (days === 1) return '1 day ago'
        if (days < 30) return `${days} days ago`
        return `${Math.floor(days / 30)}mo ago`
    }

    return (
        <div className="card job-card" onClick={() => navigate(`/jobs/${job.id}`)} style={{ cursor: 'pointer' }}>
            <div className="job-logo">
                {job.company.charAt(0).toUpperCase()}
            </div>
            <div className="job-info">
                <div className="job-title">{job.title}</div>
                <div className="job-company">{job.company}</div>
                <div className="job-meta">
                    {job.location && (
                        <span><MapPin size={12} /> {job.location}</span>
                    )}
                    {job.salary_range && (
                        <span><DollarSign size={12} /> {job.salary_range}</span>
                    )}
                    <span><Clock size={12} /> {timeAgo(job.created_at)}</span>
                    {job.source && (
                        <span className="badge badge-primary">{job.source}</span>
                    )}
                </div>
            </div>
            {score !== undefined && (
                <div style={{ textAlign: 'center' }}>
                    <div style={{
                        fontSize: '1.5rem', fontWeight: 800,
                        color: score >= 80 ? '#10b981' : score >= 60 ? '#6366f1' : '#f59e0b'
                    }}>
                        {Math.round(score)}%
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Match</div>
                </div>
            )}
        </div>
    )
}

export default JobCard
