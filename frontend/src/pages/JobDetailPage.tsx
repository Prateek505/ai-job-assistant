/**
 * Job Detail — full job info with resume optimization, cover letter, and networking tabs.
 */

import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
    ArrowLeft, MapPin, DollarSign, Clock, ExternalLink,
    Sparkles, FileText, Users, Loader2
} from 'lucide-react'
import {
    jobsAPI, Job, ResumeOptimization, CoverLetter, NetworkingSuggestion
} from '../api/endpoints'
import toast from 'react-hot-toast'

type Tab = 'details' | 'optimize' | 'cover' | 'network'

const JobDetailPage: React.FC = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const [job, setJob] = useState<Job | null>(null)
    const [tab, setTab] = useState<Tab>('details')
    const [optimization, setOptimization] = useState<ResumeOptimization | null>(null)
    const [coverLetter, setCoverLetter] = useState<CoverLetter | null>(null)
    const [networking, setNetworking] = useState<NetworkingSuggestion | null>(null)
    const [loadingTab, setLoadingTab] = useState(false)

    useEffect(() => {
        if (id) {
            jobsAPI.get(parseInt(id)).then(r => setJob(r.data)).catch(() => navigate('/jobs'))
        }
    }, [id])

    const loadTab = async (t: Tab) => {
        setTab(t)
        if (!id) return
        const jobId = parseInt(id)

        if (t === 'optimize' && !optimization) {
            setLoadingTab(true)
            try {
                const r = await jobsAPI.optimizeResume(jobId)
                setOptimization(r.data)
            } catch (e: any) {
                toast.error(e.response?.data?.detail || 'Failed to generate suggestions')
            }
            setLoadingTab(false)
        }
        if (t === 'cover' && !coverLetter) {
            setLoadingTab(true)
            try {
                const r = await jobsAPI.coverLetter(jobId)
                setCoverLetter(r.data)
            } catch (e: any) {
                toast.error(e.response?.data?.detail || 'Failed to generate cover letter')
            }
            setLoadingTab(false)
        }
        if (t === 'network' && !networking) {
            setLoadingTab(true)
            try {
                const r = await jobsAPI.networking(jobId)
                setNetworking(r.data)
            } catch (e: any) {
                toast.error(e.response?.data?.detail || 'Failed to load networking suggestions')
            }
            setLoadingTab(false)
        }
    }

    if (!job) {
        return <div className="loading-page"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
    }

    const tabs = [
        { key: 'details' as Tab, label: 'Details', icon: FileText },
        { key: 'optimize' as Tab, label: 'Resume Tips', icon: Sparkles },
        { key: 'cover' as Tab, label: 'Cover Letter', icon: FileText },
        { key: 'network' as Tab, label: 'Networking', icon: Users },
    ]

    return (
        <div className="animate-in">
            <button onClick={() => navigate('/jobs')} className="btn btn-secondary" style={{ marginBottom: 24 }}>
                <ArrowLeft size={16} /> Back to Jobs
            </button>

            {/* Job header */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                    <div className="job-logo" style={{ width: 56, height: 56, fontSize: '1.3rem' }}>
                        {job.company.charAt(0)}
                    </div>
                    <div style={{ flex: 1 }}>
                        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>{job.title}</h1>
                        <div style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>{job.company}</div>
                        <div className="job-meta">
                            {job.location && <span><MapPin size={14} /> {job.location}</span>}
                            {job.salary_range && <span><DollarSign size={14} /> {job.salary_range}</span>}
                            {job.posting_date && <span><Clock size={14} /> Posted {new Date(job.posting_date).toLocaleDateString()}</span>}
                            {job.source && <span className="badge badge-primary">{job.source}</span>}
                        </div>
                    </div>
                    {job.application_link && (
                        <a href={job.application_link} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                            <ExternalLink size={16} /> Apply Now
                        </a>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
                {tabs.map(t => (
                    <button
                        key={t.key}
                        className={`btn ${tab === t.key ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => loadTab(t.key)}
                    >
                        <t.icon size={16} /> {t.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {loadingTab ? (
                <div className="card" style={{ textAlign: 'center', padding: 60 }}>
                    <Loader2 size={32} className="spinner" style={{ margin: '0 auto 16px' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>Generating with AI...</p>
                </div>
            ) : (
                <>
                    {tab === 'details' && (
                        <div className="card">
                            <h2 style={{ marginBottom: 16 }}>Job Description</h2>
                            <div style={{
                                whiteSpace: 'pre-wrap', color: 'var(--text-secondary)',
                                lineHeight: 1.8, fontSize: '0.925rem',
                            }}>
                                {job.description || 'No description available.'}
                            </div>
                        </div>
                    )}

                    {tab === 'optimize' && optimization && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            {optimization.missing_skills.length > 0 && (
                                <div className="card">
                                    <h3 style={{ marginBottom: 12, color: 'var(--warning)' }}>⚡ Missing Skills</h3>
                                    <div className="tag-list">
                                        {optimization.missing_skills.map((s, i) => (
                                            <span key={i} className="badge badge-warning">{s}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {optimization.missing_keywords.length > 0 && (
                                <div className="card">
                                    <h3 style={{ marginBottom: 12, color: 'var(--info)' }}>🔑 Missing Keywords</h3>
                                    <div className="tag-list">
                                        {optimization.missing_keywords.map((k, i) => (
                                            <span key={i} className="badge badge-info">{k}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {optimization.suggestions.length > 0 && (
                                <div className="card">
                                    <h3 style={{ marginBottom: 12, color: 'var(--success)' }}>💡 Suggestions</h3>
                                    <ul style={{ paddingLeft: 20, color: 'var(--text-secondary)', lineHeight: 2 }}>
                                        {optimization.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}

                    {tab === 'cover' && coverLetter && (
                        <div className="card">
                            <h3 style={{ marginBottom: 16 }}>Cover Letter for {coverLetter.company}</h3>
                            <div style={{
                                whiteSpace: 'pre-wrap', lineHeight: 1.8,
                                color: 'var(--text-secondary)', fontSize: '0.925rem',
                            }}>
                                {coverLetter.cover_letter}
                            </div>
                            <button
                                className="btn btn-secondary" style={{ marginTop: 16 }}
                                onClick={() => {
                                    navigator.clipboard.writeText(coverLetter.cover_letter)
                                    toast.success('Copied to clipboard!')
                                }}
                            >
                                📋 Copy to Clipboard
                            </button>
                        </div>
                    )}

                    {tab === 'network' && networking && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            {networking.contacts.map((c, i) => (
                                <div key={i} className="card">
                                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{c.name}</div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 4 }}>
                                        {c.role} · {c.department}
                                    </div>
                                    <div style={{
                                        background: 'var(--bg-glass)', padding: 12, borderRadius: 8,
                                        fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: 8,
                                        fontStyle: 'italic',
                                    }}>
                                        "{c.connection_message}"
                                    </div>
                                </div>
                            ))}
                            {networking.tips.length > 0 && (
                                <div className="card">
                                    <h3 style={{ marginBottom: 12, color: 'var(--success)' }}>🎯 Networking Tips</h3>
                                    <ul style={{ paddingLeft: 20, color: 'var(--text-secondary)', lineHeight: 2 }}>
                                        {networking.tips.map((t, i) => <li key={i}>{t}</li>)}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default JobDetailPage
