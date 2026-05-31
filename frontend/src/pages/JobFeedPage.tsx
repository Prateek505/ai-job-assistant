/**
 * Job Feed — browse and search job listings.
 */

import React, { useEffect, useState, useRef } from 'react'
import { Search, Filter, Briefcase, Download, Loader2, X, MapPin, Building2 } from 'lucide-react'
import { jobsAPI, scrapingAPI, Job } from '../api/endpoints'
import JobCard from '../components/JobCard'
import toast from 'react-hot-toast'

// Scraper definitions with proper labels
const ATS_SCRAPERS = [
    { value: 'greenhouse', label: 'Greenhouse' },
    { value: 'lever', label: 'Lever' },
    { value: 'ashby', label: 'Ashby' },
    { value: 'smartrecruiters', label: 'SmartRecruiters' },
    { value: 'bamboohr', label: 'BambooHR' },
    { value: 'workable', label: 'Workable' },
    { value: 'jazzhr', label: 'JazzHR' },
    { value: 'workday', label: 'Workday' },
]

const JOB_BOARD_SCRAPERS = [
    { value: 'naukri', label: 'Naukri (India)' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'indeed', label: 'Indeed' },
    { value: 'glassdoor', label: 'Glassdoor' },
    { value: 'remoteok', label: 'RemoteOK' },
    { value: 'arbeitnow', label: 'Arbeitnow (EU/Remote)' },
]

const ATS_VALUES = ATS_SCRAPERS.map(s => s.value)
const LOC_BOARD_VALUES = ['linkedin', 'naukri', 'indeed', 'glassdoor']

const JobFeedPage: React.FC = () => {
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)
    const [filtering, setFiltering] = useState(false)
    const [search, setSearch] = useState('')
    const [location, setLocation] = useState('')
    const [company, setCompany] = useState('')
    const [scrapeSlug, setScrapeSlug] = useState('')
    const [scrapeLocation, setScrapeLocation] = useState('')
    const [scrapeType, setScrapeType] = useState<string>('naukri')
    const [scraping, setScraping] = useState(false)
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const isJobBoard = !ATS_VALUES.includes(scrapeType)
    const hasLocationParam = LOC_BOARD_VALUES.includes(scrapeType)

    useEffect(() => { loadJobs() }, [])

    const loadJobs = async (params?: { search?: string; location?: string; company?: string }) => {
        setLoading(true)
        try {
            const res = await jobsAPI.list(params)
            setJobs(res.data)
        } catch { /* empty */ }
        setLoading(false)
        setFiltering(false)
    }

    // Debounced live filtering — triggers 400ms after user stops typing
    const triggerFilter = (newSearch: string, newLocation: string, newCompany: string) => {
        if (debounceRef.current) clearTimeout(debounceRef.current)
        setFiltering(true)
        debounceRef.current = setTimeout(() => {
            loadJobs({
                search: newSearch || undefined,
                location: newLocation || undefined,
                company: newCompany || undefined,
            })
        }, 400)
    }

    const handleSearchChange = (val: string) => { setSearch(val); triggerFilter(val, location, company) }
    const handleLocationChange = (val: string) => { setLocation(val); triggerFilter(search, val, company) }
    const handleCompanyChange = (val: string) => { setCompany(val); triggerFilter(search, location, val) }

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        loadJobs({ search: search || undefined, location: location || undefined, company: company || undefined })
    }

    const clearFilters = () => {
        setSearch(''); setLocation(''); setCompany('')
        loadJobs()
    }
    const hasFilters = search || location || company

    const handleScrape = async () => {
        if (!scrapeSlug.trim()) return
        setScraping(true)
        try {
            let res
            if (ATS_VALUES.includes(scrapeType)) {
                const fn = scrapingAPI[scrapeType as keyof typeof scrapingAPI] as (slug: string) => Promise<any>
                res = await fn(scrapeSlug.trim())
            } else if (LOC_BOARD_VALUES.includes(scrapeType)) {
                const fn = scrapingAPI[scrapeType as keyof typeof scrapingAPI] as (kw: string, loc: string) => Promise<any>
                res = await fn(scrapeSlug.trim(), scrapeLocation.trim())
            } else {
                const fn = scrapingAPI[scrapeType as keyof typeof scrapingAPI] as (kw: string) => Promise<any>
                res = await fn(scrapeSlug.trim())
            }
            const data = res.data
            if (data.success) {
                toast.success(`✅ Found ${data.jobs_found} jobs (${data.new_jobs ?? 0} new added to DB)`)
                await loadJobs()
            } else {
                toast.error(data.error || data.message || 'Scraping failed')
            }
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Scraping failed. Check if playwright is installed.')
        }
        setScraping(false)
    }

    return (
        <div className="animate-in">
            <div className="page-header">
                <h1>Job Feed</h1>
                <p>Discover jobs sourced from top companies. Use the scraper below to pull live listings.</p>
            </div>

            {/* ── Scrape Panel ── */}
            <div className="card" style={{ marginBottom: 24, padding: '20px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                    <Download size={18} color="var(--accent)" />
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Scrape Jobs</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: 4 }}>
                        — pull real listings into your database
                    </span>
                </div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    {/* Platform selector */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Platform</label>
                        <select
                            className="input"
                            value={scrapeType}
                            onChange={e => setScrapeType(e.target.value)}
                            style={{ width: 190, fontSize: '0.875rem' }}
                        >
                            <optgroup label="🇮🇳 Indian Job Boards">
                                <option value="naukri">Naukri.com (India)</option>
                            </optgroup>
                            <optgroup label="🌐 Global Job Boards">
                                {JOB_BOARD_SCRAPERS.filter(s => s.value !== 'naukri').map(s => (
                                    <option key={s.value} value={s.value}>{s.label}</option>
                                ))}
                            </optgroup>
                            <optgroup label="🏢 ATS Platforms (Company Slug)">
                                {ATS_SCRAPERS.map(s => (
                                    <option key={s.value} value={s.value}>{s.label}</option>
                                ))}
                            </optgroup>
                        </select>
                    </div>

                    {/* Keywords / slug input */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 170 }}>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                            {isJobBoard ? 'Keywords' : 'Company Slug'}
                        </label>
                        <input
                            className="input"
                            placeholder={isJobBoard
                                ? (scrapeType === 'naukri' ? 'e.g. python developer, data analyst' : 'e.g. software engineer')
                                : 'e.g. figma, stripe, notion'}
                            value={scrapeSlug}
                            onChange={e => setScrapeSlug(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleScrape()}
                        />
                    </div>

                    {/* Location input (only for boards that support it) */}
                    {hasLocationParam && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: 160 }}>
                            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Location</label>
                            <input
                                className="input"
                                placeholder={scrapeType === 'naukri' ? 'e.g. Bangalore, India' : 'e.g. United States'}
                                value={scrapeLocation}
                                onChange={e => setScrapeLocation(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleScrape()}
                            />
                        </div>
                    )}

                    <button
                        className="btn btn-primary"
                        onClick={handleScrape}
                        disabled={scraping || !scrapeSlug.trim()}
                        style={{ alignSelf: 'flex-end' }}
                    >
                        {scraping ? <Loader2 size={16} style={{ animation: 'spin 0.8s linear infinite' }} /> : <Download size={16} />}
                        {scraping ? 'Fetching...' : isJobBoard ? 'Fetch Jobs' : 'Scrape'}
                    </button>
                </div>
                {scrapeType === 'naukri' && (
                    <div style={{ marginTop: 10, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        💡 Tip: Try keywords like <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>python developer</code>,{' '}
                        <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>software engineer</code>, location{' '}
                        <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>bangalore</code> or <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>india</code>
                    </div>
                )}
                {ATS_VALUES.includes(scrapeType) && (
                    <div style={{ marginTop: 10, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        💡 Use the company's career page slug. Examples for {scrapeType === 'greenhouse' ? 'Greenhouse' : scrapeType === 'lever' ? 'Lever' : scrapeType}:{' '}
                        {scrapeType === 'greenhouse' && <><code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>figma</code>, <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>stripe</code>, <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>vercel</code></>}
                        {scrapeType === 'lever' && <><code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>anyscale</code>, <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>coinbase</code></>}
                        {scrapeType === 'ashby' && <><code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>linear</code>, <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>raycast</code></>}
                        {['smartrecruiters', 'bamboohr', 'workable', 'jazzhr', 'workday'].includes(scrapeType) && <code style={{ background: 'var(--bg-glass)', padding: '1px 5px', borderRadius: 4 }}>company-name</code>}
                    </div>
                )}
            </div>

            {/* ── Filter Bar ── */}
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 10, marginBottom: 28, flexWrap: 'wrap', alignItems: 'center' }}>
                {/* Search input */}
                <div style={{ flex: 2, minWidth: 200, position: 'relative' }}>
                    <Search size={16} style={{
                        position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
                        color: 'var(--text-muted)', pointerEvents: 'none',
                    }} />
                    <input
                        className="input" placeholder="Search by title or keyword…"
                        value={search} onChange={e => handleSearchChange(e.target.value)}
                        style={{ width: '100%', paddingLeft: 38 }}
                    />
                </div>

                {/* Location filter */}
                <div style={{ flex: 1, minWidth: 140, position: 'relative' }}>
                    <MapPin size={14} style={{
                        position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
                        color: 'var(--text-muted)', pointerEvents: 'none',
                    }} />
                    <input
                        className="input"
                        placeholder="Location (e.g. India, Remote)"
                        value={location}
                        onChange={e => handleLocationChange(e.target.value)}
                        style={{ paddingLeft: 30 }}
                    />
                </div>

                {/* Company filter */}
                <div style={{ flex: 1, minWidth: 130, position: 'relative' }}>
                    <Building2 size={14} style={{
                        position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
                        color: 'var(--text-muted)', pointerEvents: 'none',
                    }} />
                    <input
                        className="input"
                        placeholder="Company"
                        value={company}
                        onChange={e => handleCompanyChange(e.target.value)}
                        style={{ paddingLeft: 30 }}
                    />
                </div>

                <button type="submit" className="btn btn-primary" style={{ flexShrink: 0 }}>
                    {filtering ? <Loader2 size={14} style={{ animation: 'spin 0.8s linear infinite' }} /> : <Filter size={14} />}
                    Filter
                </button>

                {hasFilters && (
                    <button type="button" className="btn btn-secondary" onClick={clearFilters} style={{ flexShrink: 0 }}>
                        <X size={14} /> Clear
                    </button>
                )}
            </form>

            {/* Active filter pills */}
            {hasFilters && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                    {search && <span className="badge badge-primary">🔍 "{search}"</span>}
                    {location && <span className="badge badge-info">📍 {location}</span>}
                    {company && <span className="badge badge-warning">🏢 {company}</span>}
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                        {jobs.length} result{jobs.length !== 1 ? 's' : ''}
                    </span>
                </div>
            )}

            {/* Job list */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: 60 }}>
                    <div className="spinner" style={{ width: 32, height: 32 }} />
                </div>
            ) : jobs.length === 0 ? (
                <div className="card empty-state">
                    <Briefcase size={64} />
                    <h3>No jobs found</h3>
                    <p>
                        {hasFilters
                            ? `No jobs match your filters. Try a different keyword or location.`
                            : 'Use the scraper above to pull jobs from Naukri, Greenhouse, Lever and more.'}
                    </p>
                    {hasFilters && (
                        <button className="btn btn-secondary" onClick={clearFilters} style={{ marginTop: 16 }}>
                            <X size={14} /> Clear Filters
                        </button>
                    )}
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {jobs.map(job => (
                        <JobCard key={job.id} job={job} />
                    ))}
                </div>
            )}
        </div>
    )
}

export default JobFeedPage
