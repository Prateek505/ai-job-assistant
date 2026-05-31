/**
 * Typed API endpoint functions.
 * Each function calls the backend and returns typed data.
 */

import api from './client'

// ── Types ────────────────────────────────────────────────

export interface User {
    id: number
    email: string
    name: string
    created_at: string
}

export interface Resume {
    id: number
    filename: string
    raw_text: string
    parsed_json: {
        skills?: string[]
        technologies?: string[]
        experience?: { title: string; company: string; duration: string }[]
        education?: { degree: string; institution: string }[]
        projects?: { name: string; description: string }[]
    }
    uploaded_at: string
}

export interface Preference {
    id: number
    user_id: number
    role_titles: string[]
    locations: string[]
    salary_min: number | null
    salary_max: number | null
    experience_level: string | null
    remote_preference: string | null
    priority_companies: string[]
}

export interface Job {
    id: number
    title: string
    company: string
    description: string
    location: string | null
    salary_range: string | null
    posting_date: string | null
    deadline: string | null
    application_link: string | null
    source: string | null
    created_at: string
}

export interface JobMatch {
    id: number
    job_id: number
    score: number
    skill_similarity: number
    experience_match: number
    location_preference: number
    salary_preference: number
    company_priority: number
    status: string
    created_at: string
    job: Job | null
}

export interface Notification {
    id: number
    type: string
    title: string
    message: string
    read: boolean
    job_id: number | null
    created_at: string
}

export interface ResumeOptimization {
    missing_keywords: string[]
    missing_skills: string[]
    suggestions: string[]
    optimized_text: string
}

export interface CoverLetter {
    cover_letter: string
    job_title: string
    company: string
}

export interface NetworkingContact {
    name: string
    role: string
    department: string
    connection_message: string
}

export interface NetworkingSuggestion {
    company: string
    contacts: NetworkingContact[]
    tips: string[]
}

// ── Auth ─────────────────────────────────────────────────

export const authAPI = {
    register: (data: { email: string; password: string; name: string }) =>
        api.post<{ access_token: string }>('/auth/register', data),
    login: (data: { email: string; password: string }) =>
        api.post<{ access_token: string }>('/auth/login', data),
    me: () => api.get<User>('/auth/me'),
}

// ── Resumes ──────────────────────────────────────────────

export const resumeAPI = {
    list: () => api.get<Resume[]>('/resumes/'),
    upload: (file: File) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post<Resume>('/resumes/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },
    get: (id: number) => api.get<Resume>(`/resumes/${id}`),
}

// ── Preferences ──────────────────────────────────────────

export const preferencesAPI = {
    get: () => api.get<Preference>('/preferences/'),
    update: (data: Omit<Preference, 'id' | 'user_id'>) =>
        api.put<Preference>('/preferences/', data),
}

// ── Jobs ─────────────────────────────────────────────────

export const jobsAPI = {
    list: (params?: { search?: string; location?: string; company?: string; skip?: number; limit?: number }) =>
        api.get<Job[]>('/jobs/', { params }),
    get: (id: number) => api.get<Job>(`/jobs/${id}`),
    create: (data: Partial<Job>) => api.post<Job>('/jobs/', data),
    optimizeResume: (id: number) => api.get<ResumeOptimization>(`/jobs/${id}/optimize-resume`),
    coverLetter: (id: number) => api.get<CoverLetter>(`/jobs/${id}/cover-letter`),
    networking: (id: number) => api.get<NetworkingSuggestion>(`/jobs/${id}/networking`),
}

// ── Matches ──────────────────────────────────────────────

export const matchesAPI = {
    list: () => api.get<JobMatch[]>('/matches/'),
    refresh: () => api.post<{ message: string; matches_created: number }>('/matches/refresh'),
    updateStatus: (id: number, status: string) =>
        api.put<JobMatch>(`/matches/${id}/status`, { status }),
}

// ── Notifications ────────────────────────────────────────

export const notificationsAPI = {
    list: () => api.get<Notification[]>('/notifications/'),
    markRead: (id: number) => api.put<Notification>(`/notifications/${id}/read`),
}

// ── Scraping ─────────────────────────────────────────────

export interface ScrapeResponse {
    success: boolean
    message: string
    scraper_type: string
    jobs_found: number
    new_jobs?: number
    updated_jobs?: number
    skipped_jobs?: number
    error?: string
}

export const scrapingAPI = {
    greenhouse: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/greenhouse', { company_slug }),
    lever: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/lever', { company_slug }),
    linkedin: (keywords: string, location: string) =>
        api.post<ScrapeResponse>('/scraping/linkedin', { keywords, location }),
    naukri: (keywords: string, location: string) =>
        api.post<ScrapeResponse>('/scraping/naukri', { keywords, location }),
    indeed: (keywords: string, location: string) =>
        api.post<ScrapeResponse>('/scraping/indeed', { keywords, location }),
    glassdoor: (keywords: string, location: string) =>
        api.post<ScrapeResponse>('/scraping/glassdoor', { keywords, location }),
    remoteok: (keywords: string) =>
        api.post<ScrapeResponse>('/scraping/remoteok', { keywords }),
    arbeitnow: (keywords: string) =>
        api.post<ScrapeResponse>('/scraping/arbeitnow', { keywords }),
    ashby: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/ashby', { company_slug }),
    smartrecruiters: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/smartrecruiters', { company_slug }),
    bamboohr: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/bamboohr', { company_slug }),
    workable: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/workable', { company_slug }),
    jazzhr: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/jazzhr', { company_slug }),
    workday: (company_slug: string) =>
        api.post<ScrapeResponse>('/scraping/workday', { company_slug }),
    careerPage: (url: string, company_name: string) =>
        api.post<ScrapeResponse>('/scraping/career-page', { url, company_name }),
    status: () => api.get('/scraping/status'),
}
