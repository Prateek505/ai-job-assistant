/**
 * Job Feed — browse and search job listings.
 */

import React, { useEffect, useState, useRef } from 'react'
import { Search, Filter, Briefcase, Download, Loader2, X, MapPin, Building2, Globe } from 'lucide-react'
import { jobsAPI, scrapingAPI, Job } from '../api/endpoints'
import JobCard from '../components/JobCard'
import toast from 'react-hot-toast'

// All scraper types that support keyword + location
const KEYWORD_SCRAPERS = ['naukri', 'linkedin', 'indeed', 'glassdoor']
// All scraper types that support keyword only (no location param)
const KEYWORD_ONLY_SCRAPERS = ['remoteok', 'arbeitnow']

const JobFeedPage: React.FC = () => {
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)
    const [filtering, setFiltering] = useState(false)
    const [search, setSearch] = useState('')
    const [location, setLocation] = useState('')
    const [company, setCompany] = useState('')

    // Scrape panel — just keywords + location, no platform dropdown
    const [scrapeKeywords, setScrapeKeywords] = useState('')
    const [scrapeLocation, setScrapeLocation] = useState('')
    const [scraping, setScraping] = useState(false)
    const [scrapeProgress, setScrapeProgress] = useState<string[]>([])

    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

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

    // Debounced live filtering
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

    // Scrape ALL platforms simultaneously with the given keywords + location
    const handleScrapeAll = async () => {
        const kw = scrapeKeywords.trim()
        if (!kw) { toast.error('Please enter keywords to search for'); return }

        setScraping(true)
        setScrapeProgress([])
        const loc = scrapeLocation.trim()

        let totalFound = 0
        let totalNew = 0
        const log = (msg: string) => setScrapeProgress(p => [...p, msg])

        // Run all scrapers in parallel
        const tasks: Promise<void>[] = [
            // Keyword + location scrapers
            ...[...KEYWORD_SCRAPERS].map(async (type) => {
                try {
                    const fn = scrapingAPI[type as keyof typeof scrapingAPI] as (kw: string, loc: string) => Promise<any>
                    const res = await fn(kw, loc)
                    const d = res.data
                    if (d.jobs_found > 0) {
                        log(`✅ ${type}: ${d.jobs_found} found, ${d.new_jobs ?? 0} new`)
                        totalFound += d.jobs_found
                        totalNew += d.new_jobs ?? 0
                    } else {
                        log(`— ${type}: no results`)
                    }
                } catch { log(`⚠️ ${type}: unavailable`) }
            }),
            // Keyword-only scrapers
            ...[...KEYWORD_ONLY_SCRAPERS].map(async (type) => {
                try {
                    const fn = scrapingAPI[type as keyof typeof scrapingAPI] as (kw: string) => Promise<any>
                    const res = await fn(kw)
                    const d = res.data
                    if (d.jobs_found > 0) {
                        log(`✅ ${type}: ${d.jobs_found} found, ${d.new_jobs ?? 0} new`)
                        totalFound += d.jobs_found
                        totalNew += d.new_jobs ?? 0
                    } else {
                        log(`— ${type}: no results`)
                    }
                } catch { log(`⚠️ ${type}: unavailable`) }
            }),
        ]

        await Promise.allSettled(tasks)

        if (totalFound > 0) {
            toast.success(`🎉 Scraped ${totalFound} jobs across all platforms — ${totalNew} new added!`)
            await loadJobs()
        } else {
            toast(`No jobs found. Try different keywords or location.`, { icon: '🔍' })
        }
        setScraping(false)
    }

    return (
        <div className="animate-in">
            <div className="page-header">
                <h1>Job Feed</h1>
                <p>Discover jobs sourced from top platforms. Enter keywords below to scrape live listings from all sites at once.</p>
            </div>

            {/* ── Scrape Panel — no platform dropdown, always scrapes all ── */}
            <div className="card" style={{ marginBottom: 24, padding: '20px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                    <Globe size={18} color="var(--accent)" />
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Scrape Jobs</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: 4 }}>
                        — searches Naukri, LinkedIn, Indeed, Glassdoor, RemoteOK &amp; Arbeitnow simultaneously
                    </span>
                </div>

                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    {/* Keywords */}
                    <div style={{ flex: 2, minWidth: 200, display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                            Keywords
                        </label>
                        <input
                            className="input"
                            placeholder="e.g. python developer, software engineer, data analyst"
                            value={scrapeKeywords}
                            onChange={e => setScrapeKeywords(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleScrapeAll()}
                        />
                    </div>

                    {/* Location */}
                    <div style={{ flex: 1, minWidth: 160, display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                            Location <span style={{ fontWeight: 400, opacity: 0.6 }}>(optional)</span>
                        </label>
                        <input
                            className="input"
                            placeholder="e.g. Bangalore, India, Remote"
                            value={scrapeLocation}
                            onChange={e => setScrapeLocation(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleScrapeAll()}
                        />
                    </div>

                    <button
                        className="btn btn-primary"
                        onClick={handleScrapeAll}
                        disabled={scraping || !scrapeKeywords.trim()}
                        style={{ alignSelf: 'flex-end', minWidth: 120 }}
                    >
                        {scraping
                            ? <><Loader2 size={16} style={{ animation: 'spin 0.8s linear infinite' }} /> Scraping…</>
                            : <><Download size={16} /> Fetch All</>
                        }
                    </button>
                </div>

                {/* Live progress log */}
                {scrapeProgress.length > 0 && (
                    <div style={{
                        marginTop: 14, padding: '10px 14px',
                        background: 'var(--bg-glass)', borderRadius: 8,
                        border: '1px solid var(--border)',
                        display: 'flex', flexDirection: 'column', gap: 4,
                    }}>
                        {scrapeProgress.map((msg, i) => (
                            <span key={i} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{msg}</span>
                        ))}
                        {scraping && (
                            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                <Loader2 size={11} style={{ animation: 'spin 0.8s linear infinite', display: 'inline', marginRight: 4 }} />
                                Waiting for remaining platforms…
                            </span>
                        )}
                    </div>
                )}

                {!scraping && scrapeProgress.length === 0 && (
                    <div style={{ marginTop: 10, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        💡 Try: <code style={{ background: 'var(--bg-glass)', padding: '1px 6px', borderRadius: 4 }}>python developer</code>{' '}
                        <code style={{ background: 'var(--bg-glass)', padding: '1px 6px', borderRadius: 4 }}>software engineer</code>{' '}
                        <code style={{ background: 'var(--bg-glass)', padding: '1px 6px', borderRadius: 4 }}>data analyst</code>
                    </div>
                )}
            </div>

            {/* ── Filter Bar ── */}
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 10, marginBottom: 28, flexWrap: 'wrap', alignItems: 'center' }}>
                <div style={{ flex: 2, minWidth: 200, position: 'relative' }}>
                    <Search size={16} style={{
                        position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
                        color: 'var(--text-muted)', pointerEvents: 'none',
                    }} />
                    <input
                        className="input" placeholder="Search by title, keyword or company…"
                        value={search} onChange={e => handleSearchChange(e.target.value)}
                        style={{ width: '100%', paddingLeft: 38 }}
                    />
                </div>

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
                            : 'Use the scraper above to pull live jobs from Naukri, LinkedIn, Indeed and more.'}
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
