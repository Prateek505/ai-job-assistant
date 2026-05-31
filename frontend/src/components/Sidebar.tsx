/**
 * Sidebar navigation — shown on all authenticated pages.
 * Uses lucide-react icons and react-router-dom for navigation.
 */

import React from 'react'
import { NavLink } from 'react-router-dom'
import {
    LayoutDashboard, FileText, Briefcase, Trophy, Users,
    Bell, Settings, LogOut, Sparkles
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/resumes', icon: FileText, label: 'Resume Manager' },
    { to: '/jobs', icon: Briefcase, label: 'Job Feed' },
    { to: '/rankings', icon: Trophy, label: 'Job Rankings' },
    { to: '/networking', icon: Users, label: 'Networking' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
    { to: '/preferences', icon: Settings, label: 'Preferences' },
]

const Sidebar: React.FC = () => {
    const { user, logout } = useAuth()

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="logo-icon">
                    <Sparkles size={20} color="white" />
                </div>
                <h1>JobAI</h1>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                        end={item.to === '/'}
                    >
                        <item.icon size={20} />
                        {item.label}
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div style={{ marginBottom: '12px', fontSize: '0.875rem' }}>
                    <div style={{ fontWeight: 600 }}>{user?.name || 'User'}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{user?.email}</div>
                </div>
                <button className="nav-item" onClick={logout} style={{ width: '100%' }}>
                    <LogOut size={18} />
                    Sign Out
                </button>
            </div>
        </aside>
    )
}

export default Sidebar
