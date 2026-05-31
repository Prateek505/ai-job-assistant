/**
 * Login / Register page with animated gradient background.
 */

import React, { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

const LoginPage: React.FC = () => {
    const { login, register } = useAuth()
    const [isRegister, setIsRegister] = useState(false)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        try {
            if (isRegister) {
                await register(email, password, name)
                toast.success('Account created successfully!')
            } else {
                await login(email, password)
                toast.success('Welcome back!')
            }
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Something went wrong')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card animate-in">
                <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                    <div style={{
                        width: 56, height: 56, borderRadius: 16,
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        boxShadow: '0 0 30px rgba(99, 102, 241, 0.4)',
                        marginBottom: 16,
                    }}>
                        <Sparkles size={28} color="white" />
                    </div>
                </div>
                <h1>{isRegister ? 'Create Account' : 'Welcome Back'}</h1>
                <p className="subtitle">
                    {isRegister
                        ? 'Start discovering your dream job with AI'
                        : 'Sign in to your AI Job Assistant'}
                </p>

                <form onSubmit={handleSubmit}>
                    {isRegister && (
                        <div className="input-group">
                            <label htmlFor="name">Full Name</label>
                            <input
                                id="name" type="text" className="input"
                                placeholder="John Doe"
                                value={name} onChange={(e) => setName(e.target.value)}
                                required
                            />
                        </div>
                    )}
                    <div className="input-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email" type="email" className="input"
                            placeholder="you@example.com"
                            value={email} onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password" type="password" className="input"
                            placeholder="••••••••"
                            value={password} onChange={(e) => setPassword(e.target.value)}
                            required minLength={6}
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? <span className="spinner" /> : (isRegister ? 'Create Account' : 'Sign In')}
                    </button>
                </form>

                <div className="auth-toggle">
                    {isRegister ? 'Already have an account? ' : "Don't have an account? "}
                    <button onClick={() => setIsRegister(!isRegister)}>
                        {isRegister ? 'Sign In' : 'Create one'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default LoginPage
