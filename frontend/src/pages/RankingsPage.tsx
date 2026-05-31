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

                            {/* Status selector */}
                            <select
                                className="input"
                                value={match.status}
                                onChange={e => updateStatus(match.id, e.target.value)}
                                style={{ width: 120, fontSize: '0.8rem' }}
                            >
                                <option value="new">New</option>
                                <option value="saved">Saved</option>
                                <option value="applied">Applied</option>
                                <option value="rejected">Rejected</option>
                            </select>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default RankingsPage
