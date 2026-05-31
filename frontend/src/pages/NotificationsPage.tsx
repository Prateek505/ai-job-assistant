import React, { useEffect, useState } from 'react'
import { Bell, Check, Briefcase, AlertTriangle, Star } from 'lucide-react'
import { notificationsAPI, Notification } from '../api/endpoints'
import toast from 'react-hot-toast'

const NotificationsPage: React.FC = () => {
    const [notifs, setNotifs] = useState<Notification[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        notificationsAPI.list().then(r => { setNotifs(r.data); setLoading(false) }).catch(() => setLoading(false))
    }, [])

    const markRead = async (id: number) => {
        try {
            await notificationsAPI.markRead(id)
            setNotifs(p => p.map(n => n.id === id ? { ...n, read: true } : n))
        } catch { toast.error('Failed') }
    }

    const icon = (t: string) => {
        if (t === 'new_job') return <Briefcase size={18} color="var(--info)" />
        if (t === 'deadline') return <AlertTriangle size={18} color="var(--warning)" />
        if (t === 'priority_company') return <Star size={18} color="var(--accent)" />
        return <Bell size={18} color="var(--text-muted)" />
    }

    if (loading) return <div className="loading-page"><div className="spinner" /></div>

    return (
        <div className="animate-in">
            <div className="page-header"><h1>Notifications</h1><p>Stay updated on new jobs and deadlines</p></div>
            {notifs.length === 0 ? (
                <div className="card empty-state"><Bell size={64} /><h3>No notifications</h3><p>You're all caught up!</p></div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {notifs.map(n => (
                        <div key={n.id} className={`card notification-item ${n.read ? '' : 'unread'}`} style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
                            {icon(n.type)}
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600 }}>{n.title}</div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 2 }}>{n.message}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>{new Date(n.created_at).toLocaleString()}</div>
                            </div>
                            {!n.read && <button className="btn btn-secondary btn-sm" onClick={() => markRead(n.id)}><Check size={14} /> Read</button>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default NotificationsPage
