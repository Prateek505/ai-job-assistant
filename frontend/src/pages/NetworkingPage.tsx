/**
 * Networking — suggestions for companies in your matched jobs.
 */

import React, { useEffect, useState } from 'react'
import { Users, MessageSquare, Target } from 'lucide-react'
import { matchesAPI, jobsAPI, JobMatch, NetworkingSuggestion } from '../api/endpoints'
import toast from 'react-hot-toast'

const NetworkingPage: React.FC = () => {
    const [matches, setMatches] = useState<JobMatch[]>([])
    const [suggestions, setSuggestions] = useState<{ [key: number]: NetworkingSuggestion }>({})
    const [loading, setLoading] = useState(true)
    const [loadingId, setLoadingId] = useState<number | null>(null)

    useEffect(() => {
        matchesAPI.list().then(r => {
            setMatches(r.data.filter(m => m.job).slice(0, 10))
            setLoading(false)
        }).catch(() => setLoading(false))
    }, [])

    const loadNetworking = async (jobId: number) => {
        if (suggestions[jobId]) return
        setLoadingId(jobId)
        try {
            const r = await jobsAPI.networking(jobId)
            setSuggestions(prev => ({ ...prev, [jobId]: r.data }))
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Failed to load')
        }
        setLoadingId(null)
    }

    if (loading) {
        return <div className="loading-page"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
    }

    return (
        <div className="animate-in">
            <div className="page-header">
                <h1>Networking Assistant</h1>
                <p>Find relevant contacts and craft connection messages for your target companies</p>
            </div>

            {matches.length === 0 ? (
                <div className="card empty-state">
                    <Users size={64} />
                    <h3>No companies to network with</h3>
                    <p>Get job matches first, then explore networking tips for each company</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {matches.map(m => m.job && (
                        <div key={m.id} className="card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: suggestions[m.job_id] ? 16 : 0 }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '1rem' }}>{m.job.company}</div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{m.job.title}</div>
                                </div>
                                <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={() => loadNetworking(m.job_id)}
                                    disabled={loadingId === m.job_id}
                                >
                                    {loadingId === m.job_id ? (
                                        <div className="spinner" />
                                    ) : suggestions[m.job_id] ? (
                                        <><Users size={14} /> Loaded</>
                                    ) : (
                                        <><Users size={14} /> Get Contacts</>
                                    )}
                                </button>
                            </div>

                            {suggestions[m.job_id] && (
                                <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                        {suggestions[m.job_id].contacts.map((c, i) => (
                                            <div key={i} style={{
                                                background: 'var(--bg-glass)', borderRadius: 12, padding: 16,
                                            }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                                    <MessageSquare size={14} color="var(--accent)" />
                                                    <span style={{ fontWeight: 600 }}>{c.name}</span>
                                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                                        · {c.role} · {c.department}
                                                    </span>
                                                </div>
                                                <div style={{
                                                    fontSize: '0.875rem', color: 'var(--text-secondary)',
                                                    fontStyle: 'italic', paddingLeft: 22,
                                                }}>
                                                    "{c.connection_message}"
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    {suggestions[m.job_id].tips.length > 0 && (
                                        <div style={{ marginTop: 12 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color: 'var(--success)' }}>
                                                <Target size={14} /> <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Tips</span>
                                            </div>
                                            <ul style={{ paddingLeft: 20, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                                                {suggestions[m.job_id].tips.map((t, i) => <li key={i}>{t}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default NetworkingPage
