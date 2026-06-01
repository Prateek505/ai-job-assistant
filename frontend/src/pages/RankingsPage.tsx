/**
 * Rankings — ranked job matches with score breakdown.
 */

import React, { useEffect, useState } from 'react'
import { Trophy, RefreshCw, Loader2 } from 'lucide-react'
import { matchesAPI, JobMatch } from '../api/endpoints'
import JobCard from '../components/JobCard'
import MatchScore from '../components/MatchScore'
import toast from 'react-hot-toast'

const RankingsPage: React.FC = () => {
    const [matches, setMatches] = useState<JobMatch[]>([])
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)

    useEffect(() => {
        loadMatches()
    }, [])

    const loadMatches = async () => {
        try {
            const res = await matchesAPI.list()
            setMatches(res.data)
        } catch { /* empty */ }
        setLoading(false)
    }

    const handleRefresh = async () => {
        setRefreshing(true)
        try {
            const res = await matchesAPI.refresh()
            toast.success(`${res.data.matches_created} matches computed!`)
            await loadMatches()
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Refresh failed')
        }
        setRefreshing(false)
    }

    const updateStatus = async (matchId: number, status: string) => {
        try {
            await matchesAPI.updateStatus(matchId, status)
            setMatches(prev =>
                prev.map(m => m.id === matchId ? { ...m, status } : m)
            )
            toast.success(`Status updated to ${status}`)
        } catch {
            toast.error('Failed to update status')
        }
    }

    if (loading) {
        return <div className="loading-page"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
    }

    return (
        <div className="animate-in">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>Job Rankings</h1>
                    <p>AI-ranked job matches based on your resume and preferences</p>
                </div>
                <button className="btn btn-primary" onClick={handleRefresh} disabled={refreshing}>
                    {refreshing ? <Loader2 size={16} className="spinner" /> : <RefreshCw size={16} />}
                    Refresh Matches
                </button>
            </div>

            {matches.length === 0 ? (
                <div className="card empty-state">
                    <Trophy size={64} />
                    <h3>No matches yet</h3>
                    <p>Upload a resume, add jobs, then click "Refresh Matches" to see your AI rankings</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {matches.map((match, idx) => (
                        <div key={match.id} className="card" style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
                            <div style={{
                                width: 36, height: 36, borderRadius: '50%',
                                background: 'var(--gradient-primary)', display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                                fontWeight: 700, fontSize: '0.875rem', flexShrink: 0,
                            }}>
                                #{idx + 1}
                            </div>

                            <MatchScore score={match.score} size={56} strokeWidth={4} />

                            <div style={{ flex: 1 }}>
                                {match.job && <JobCard job={match.job} />}
                            </div>

                            {/* Score breakdown */}
                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', minWidth: 200 }}>
                                {[
                                    { label: 'Skill', value: match.skill_similarity, color: '#6366f1' },
                                    { label: 'Exp', value: match.experience_match, color: '#3b82f6' },
                                    { label: 'Loc', value: match.location_preference, color: '#10b981' },
                                    { label: 'Sal', value: match.salary_preference, color: '#f59e0b' },
                                    { label: 'Co.', value: match.company_priority, color: '#8b5cf6' },
                                ].map(s => (
                                    <div key={s.label} style={{ textAlign: 'center', minWidth: 36 }}>
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{s.label}</div>
                                        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: s.color }}>
                                            {Math.round(s.value)}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Status selector — styled pill buttons, no white native dropdown */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0 }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: 2 }}>Status</div>
                                <div style={{ display: 'flex', gap: 4 }}>
                                    {[
                                        { value: 'new',      label: 'New',     color: '#6366f1', bg: 'rgba(99,102,241,0.15)' },
                                        { value: 'saved',    label: 'Saved',   color: '#3b82f6', bg: 'rgba(59,130,246,0.15)' },
                                        { value: 'applied',  label: 'Applied', color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
                                        { value: 'rejected', label: 'Reject',  color: '#ef4444', bg: 'rgba(239,68,68,0.15)' },
                                    ].map(opt => (
                                        <button
                                            key={opt.value}
                                            onClick={() => updateStatus(match.id, opt.value)}
                                            title={opt.label}
                                            style={{
                                                padding: '4px 8px',
                                                borderRadius: 6,
                                                border: match.status === opt.value
                                                    ? `1.5px solid ${opt.color}`
                                                    : '1.5px solid transparent',
                                                background: match.status === opt.value ? opt.bg : 'var(--bg-glass)',
                                                color: match.status === opt.value ? opt.color : 'var(--text-muted)',
                                                fontSize: '0.7rem',
                                                fontWeight: match.status === opt.value ? 700 : 400,
                                                cursor: 'pointer',
                                                transition: 'all 0.15s ease',
                                                whiteSpace: 'nowrap',
                                            }}
                                        >
                                            {opt.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default RankingsPage
