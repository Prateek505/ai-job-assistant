/**
 * Auth context — manages authentication state across the app.
 * Stores JWT in localStorage and provides login/logout/register functions.
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { authAPI, User } from '../api/endpoints'

interface AuthState {
    user: User | null
    token: string | null
    loading: boolean
    login: (email: string, password: string) => Promise<void>
    register: (email: string, password: string, name: string) => Promise<void>
    logout: () => void
}

const AuthContext = createContext<AuthState | undefined>(undefined)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null)
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
    const [loading, setLoading] = useState(true)

    // On mount, try to load user from stored token
    useEffect(() => {
        const loadUser = async () => {
            if (token) {
                try {
                    const res = await authAPI.me()
                    setUser(res.data)
                } catch {
                    localStorage.removeItem('token')
                    setToken(null)
                }
            }
            setLoading(false)
        }
        loadUser()
    }, [token])

    const login = async (email: string, password: string) => {
        const res = await authAPI.login({ email, password })
        const t = res.data.access_token
        localStorage.setItem('token', t)
        setToken(t)
    }

    const register = async (email: string, password: string, name: string) => {
        const res = await authAPI.register({ email, password, name })
        const t = res.data.access_token
        localStorage.setItem('token', t)
        setToken(t)
    }

    const logout = () => {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
    }

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used within AuthProvider')
    return ctx
}
