/**
 * App — root component with routing and auth guard.
 */

import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ResumePage from './pages/ResumePage'
import JobFeedPage from './pages/JobFeedPage'
import JobDetailPage from './pages/JobDetailPage'
import RankingsPage from './pages/RankingsPage'
import NetworkingPage from './pages/NetworkingPage'
import NotificationsPage from './pages/NotificationsPage'
import PreferencesPage from './pages/PreferencesPage'

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { token, loading } = useAuth()
    if (loading) {
        return (
            <div className="loading-page">
                <div className="spinner" style={{ width: 32, height: 32 }} />
                <span style={{ color: 'var(--text-secondary)' }}>Loading...</span>
            </div>
        )
    }
    if (!token) return <Navigate to="/login" />
    return <>{children}</>
}

const AppRoutes: React.FC = () => {
    const { token, loading } = useAuth()

    if (loading) {
        return (
            <div className="loading-page">
                <div className="spinner" style={{ width: 32, height: 32 }} />
            </div>
        )
    }

    if (!token) {
        return (
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
        )
    }

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <Routes>
                    <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                    <Route path="/resumes" element={<ProtectedRoute><ResumePage /></ProtectedRoute>} />
                    <Route path="/jobs" element={<ProtectedRoute><JobFeedPage /></ProtectedRoute>} />
                    <Route path="/jobs/:id" element={<ProtectedRoute><JobDetailPage /></ProtectedRoute>} />
                    <Route path="/rankings" element={<ProtectedRoute><RankingsPage /></ProtectedRoute>} />
                    <Route path="/networking" element={<ProtectedRoute><NetworkingPage /></ProtectedRoute>} />
                    <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
                    <Route path="/preferences" element={<ProtectedRoute><PreferencesPage /></ProtectedRoute>} />
                    <Route path="/login" element={<Navigate to="/" />} />
                    <Route path="*" element={<Navigate to="/" />} />
                </Routes>
            </main>
        </div>
    )
}

const App: React.FC = () => (
    <AuthProvider>
        <AppRoutes />
    </AuthProvider>
)

export default App
