/**
 * Dashboard — overview with stats, top matches, and recent notifications.
 */

import React, { useEffect, useState } from 'react'
import {
    Briefcase, FileText, Trophy, Bell, TrendingUp, RefreshCw
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import {
    resumeAPI, jobsAPI, matchesAPI, notificationsAPI,
    Resume, Job, JobMatch, Notification
} from '../api/endpoints'
import JobCard from '../components/JobCard'
import MatchScore from '../components/MatchScore'

const DashboardPage: React.FC = () => {
    const { user } = useAuth()
    const [resumes, setResumes] = useState<Resume[]>([])
    const [jobs, setJobs] = useState<Job[]>([])
    const [matches, setMatches] = useState<JobMatch[]>([])
    const [notifications, setNotifications] = useState<Notification[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const load = async () => {
            try {
                const [r, j, m, n] = await Promise.all([
                    resumeAPI.list(),
                    jobsAPI.list({ limit: 5 }),
                    matchesAPI.list(),
                    notificationsAPI.list(),
                ])
                setResumes(r.data)
                setJobs(j.data)
                setMatches(m.data)
                setNotifications(n.data)
            } catch { /* Ignore — empty states will show */ }
            setLoading(false)
        }
        load()
    }, [])

    const unreadCount = notifications.filter(n => !n.read).length
    const topMatches = matches.slice(0, 3)
    const avgScore = matches.length
        ? Math.round(matches.reduce((s, m) => s + m.score, 0) / matches.length)
        : 0

    if (loading) {
        return (
            <div className="loading-page">
                <div className="spinner" style={{ width: 32, height: 32 }} />
            </div>
        )
    }

    return (
        <div className="animate-in">
            <div className="page-header">
                <h1>Welcome back, {user?.name?.split(' ')[0]} 👋</h1>
                <p>Here's your job search overview</p>
            </div>

            {/* Stats Row */}
            <div className="grid grid-4" style={{ marginBottom: 32 }}>
                {[
                    { icon: FileText, label: 'Resumes', value: resumes.length, color: '#6366f1', bg: 'rgba(99,102,241,0.15)' },
                    { icon: Briefcase, label: 'Jobs Found', value: jobs.length, color: '#3b82f6', bg: 'rgba(59,130,246,0.15)' },
                    { icon: Trophy, label: 'Matches', value: matches.length, color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
                    { icon: Bell, label: 'Unread Alerts', value: unreadCount, color: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
                ].map((stat, i) => (
                    <div key={i} className={`card stat-card animate-in animate-in-delay-${i + 1}`}>
                        <div className="stat-icon" style={{ background: stat.bg }}>
                            <stat.icon size={24} color={stat.color} />
                        </div>
                        <div className="stat-value">{stat.value}</div>
                        <div className="stat-label">{stat.label}</div>
                    </div>
                ))}
            </div>

            <div className="grid grid-2">
                {/* Top Matches */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <TrendingUp size={20} /> Top Matches
                        </h2>
                        {avgScore > 0 && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Avg</span>
                                <MatchScore score={avgScore} size={48} strokeWidth={4} />
                            </div>
                        )}
                    </div>
                    {topMatches.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {topMatches.map(m => m.job && (
                                <JobCard key={m.id} job={m.job} score={m.score} />
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <Trophy size={48} />
                            <h3>No matches yet</h3>
                            <p>Upload a resume and add jobs to see your matches</p>
                        </div>
                    )}
                </div>

                {/* Recent Activity */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Bell size={20} /> Recent Notifications
                        </h2>
                    </div>
                    {notifications.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {notifications.slice(0, 5).map(n => (
                                <div key={n.id} className={`notification-item ${n.read ? '' : 'unread'}`}>
                                    {!n.read && <div className="notif-dot" />}
                                    <div>
                                        <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{n.title}</div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{n.message}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <Bell size={48} />
                            <h3>No notifications</h3>
                            <p>You're all caught up!</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default DashboardPage
