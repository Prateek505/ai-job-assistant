import React, { useEffect, useState, useCallback } from 'react'
import { Settings, Save, Plus, X, Tag, MapPin, Building, Briefcase } from 'lucide-react'
import { preferencesAPI, Preference } from '../api/endpoints'
import toast from 'react-hot-toast'

// ── Tag Input Component (defined OUTSIDE so React never remounts it) ─────────

interface TagInputProps {
    label: string
    icon: React.ReactNode
    field: 'role_titles' | 'locations' | 'priority_companies'
    value: string
    onChange: (v: string) => void
    onAdd: () => void
    tags: string[]
    onRemove: (i: number) => void
    placeholder: string
}

const TagInput: React.FC<TagInputProps> = ({ label, icon, field, value, onChange, onAdd, tags, onRemove, placeholder }) => (
    <div className="input-group">
        <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {icon}
            {label}
        </label>
        <div style={{ display: 'flex', gap: 8 }}>
            <input
                id={`pref-input-${field}`}
                className="input"
                style={{ flex: 1 }}
                value={value}
                onChange={e => onChange(e.target.value)}
                placeholder={placeholder}
                onKeyDown={e => {
                    if (e.key === 'Enter') { e.preventDefault(); onAdd() }
                }}
            />
            <button
                className="btn btn-secondary btn-sm"
                onClick={onAdd}
                type="button"
                title={`Add ${label}`}
                style={{ flexShrink: 0 }}
            >
                <Plus size={14} /> Add
            </button>
        </div>
        {tags.length > 0 && (
            <div className="tag-list" style={{ marginTop: 8 }}>
                {tags.map((t, i) => (
                    <span key={i} className="tag" style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        padding: '4px 10px', fontWeight: 500,
                    }}>
                        {t}
                        <X
                            size={12}
                            style={{ cursor: 'pointer', opacity: 0.7, flexShrink: 0 }}
                            onClick={() => onRemove(i)}
                        />
                    </span>
                ))}
            </div>
        )}
        {tags.length === 0 && (
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
                Type a value and press Enter or click Add
            </p>
        )}
    </div>
)

// ── Main Page ─────────────────────────────────────────────────────────────────

const PreferencesPage: React.FC = () => {
    const [prefs, setPrefs] = useState<Partial<Preference>>({
        role_titles: [], locations: [], salary_min: null, salary_max: null,
        experience_level: '', remote_preference: 'any', priority_companies: [],
    })
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    // Separate state for each tag input — never defined inside render
    const [newRole, setNewRole] = useState('')
    const [newLoc, setNewLoc] = useState('')
    const [newCo, setNewCo] = useState('')

    useEffect(() => {
        preferencesAPI.get()
            .then(r => { setPrefs(r.data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    const save = async () => {
        setSaving(true)
        try {
            const res = await preferencesAPI.update({
                role_titles: prefs.role_titles || [],
                locations: prefs.locations || [],
                salary_min: prefs.salary_min || null,
                salary_max: prefs.salary_max || null,
                experience_level: prefs.experience_level || null,
                remote_preference: prefs.remote_preference || 'any',
                priority_companies: prefs.priority_companies || [],
            })
            setPrefs(res.data)
            toast.success('✅ Preferences saved!')
        } catch { toast.error('Save failed') }
        setSaving(false)
    }

    // Stable callbacks — won't recreate on every render
    const addTag = useCallback((field: 'role_titles' | 'locations' | 'priority_companies', value: string, setter: (v: string) => void) => {
        const trimmed = value.trim()
        if (!trimmed) return
        setPrefs(p => ({ ...p, [field]: [...(p[field] || []), trimmed] }))
        setter('')
    }, [])

    const removeTag = useCallback((field: 'role_titles' | 'locations' | 'priority_companies', idx: number) => {
        setPrefs(p => ({ ...p, [field]: (p[field] || []).filter((_, i) => i !== idx) }))
    }, [])

    if (loading) return <div className="loading-page"><div className="spinner" /></div>

    return (
        <div className="animate-in">
            <div className="page-header">
                <h1>Preferences</h1>
                <p>Configure your job search criteria for better AI matching</p>
            </div>

            <div className="card" style={{ maxWidth: 660 }}>
                <form
                    onSubmit={e => { e.preventDefault(); save() }}
                    style={{ display: 'flex', flexDirection: 'column', gap: 24 }}
                >
                    {/* Role Titles */}
                    <TagInput
                        label="Role Titles"
                        icon={<Briefcase size={14} />}
                        field="role_titles"
                        value={newRole}
                        onChange={setNewRole}
                        onAdd={() => addTag('role_titles', newRole, setNewRole)}
                        tags={prefs.role_titles || []}
                        onRemove={i => removeTag('role_titles', i)}
                        placeholder="e.g. Software Engineer, Data Analyst"
                    />

                    {/* Preferred Locations */}
                    <TagInput
                        label="Preferred Locations"
                        icon={<MapPin size={14} />}
                        field="locations"
                        value={newLoc}
                        onChange={setNewLoc}
                        onAdd={() => addTag('locations', newLoc, setNewLoc)}
                        tags={prefs.locations || []}
                        onRemove={i => removeTag('locations', i)}
                        placeholder="e.g. Bangalore, Remote, India"
                    />

                    {/* Salary Range */}
                    <div className="grid grid-2">
                        <div className="input-group">
                            <label>Min Salary (₹ / $)</label>
                            <input
                                id="pref-salary-min"
                                className="input"
                                type="number"
                                placeholder="e.g. 800000"
                                value={prefs.salary_min || ''}
                                onChange={e => setPrefs(p => ({ ...p, salary_min: e.target.value ? parseInt(e.target.value) : null }))}
                            />
                        </div>
                        <div className="input-group">
                            <label>Max Salary (₹ / $)</label>
                            <input
                                id="pref-salary-max"
                                className="input"
                                type="number"
                                placeholder="e.g. 2000000"
                                value={prefs.salary_max || ''}
                                onChange={e => setPrefs(p => ({ ...p, salary_max: e.target.value ? parseInt(e.target.value) : null }))}
                            />
                        </div>
                    </div>

                    {/* Experience & Remote */}
                    <div className="grid grid-2">
                        <div className="input-group">
                            <label>Experience Level</label>
                            <select
                                id="pref-exp-level"
                                className="input"
                                value={prefs.experience_level || ''}
                                onChange={e => setPrefs(p => ({ ...p, experience_level: e.target.value }))}
                            >
                                <option value="">Any</option>
                                <option value="intern">Intern / Fresher</option>
                                <option value="junior">Junior (0–2 yrs)</option>
                                <option value="mid">Mid-Level (2–5 yrs)</option>
                                <option value="senior">Senior (5+ yrs)</option>
                                <option value="lead">Lead / Manager</option>
                                <option value="principal">Principal / Staff</option>
                            </select>
                        </div>
                        <div className="input-group">
                            <label>Work Mode</label>
                            <select
                                id="pref-remote"
                                className="input"
                                value={prefs.remote_preference || 'any'}
                                onChange={e => setPrefs(p => ({ ...p, remote_preference: e.target.value }))}
                            >
                                <option value="any">Any</option>
                                <option value="remote">Remote Only</option>
                                <option value="onsite">On-Site Only</option>
                                <option value="hybrid">Hybrid</option>
                            </select>
                        </div>
                    </div>

                    {/* Priority Companies */}
                    <TagInput
                        label="Priority Companies"
                        icon={<Building size={14} />}
                        field="priority_companies"
                        value={newCo}
                        onChange={setNewCo}
                        onAdd={() => addTag('priority_companies', newCo, setNewCo)}
                        tags={prefs.priority_companies || []}
                        onRemove={i => removeTag('priority_companies', i)}
                        placeholder="e.g. Google, Infosys, TCS"
                    />

                    <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                        <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
                            {saving ? <div className="spinner" /> : <><Save size={18} /> Save Preferences</>}
                        </button>
                        <p style={{ marginTop: 8, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            Preferences are used to rank job matches and compute your AI match score.
                        </p>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default PreferencesPage
