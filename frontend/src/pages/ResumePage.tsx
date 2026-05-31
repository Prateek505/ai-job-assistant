/**
 * Resume Manager — upload, view, and manage resumes.
 */

import React, { useEffect, useState, useRef } from 'react'
import { Upload, FileText, Check, X, ChevronDown, ChevronUp } from 'lucide-react'
import { resumeAPI, Resume } from '../api/endpoints'
import toast from 'react-hot-toast'

const ResumePage: React.FC = () => {
    const [resumes, setResumes] = useState<Resume[]>([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [expandedId, setExpandedId] = useState<number | null>(null)
    const fileRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        loadResumes()
    }, [])

    const loadResumes = async () => {
        try {
            const res = await resumeAPI.list()
            setResumes(res.data)
        } catch { /* empty */ }
        setLoading(false)
    }

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return
        setUploading(true)
        try {
            await resumeAPI.upload(file)
            toast.success('Resume uploaded and parsed!')
            await loadResumes()
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Upload failed')
        }
        setUploading(false)
        if (fileRef.current) fileRef.current.value = ''
    }

    return (
        <div className="animate-in">
            <div className="page-header">
                <h1>Resume Manager</h1>
                <p>Upload and manage your resumes. AI will parse your skills and experience.</p>
            </div>

            {/* Upload area */}
            <div className="card" style={{
                border: '2px dashed var(--border)',
                textAlign: 'center',
                padding: '48px 24px',
                marginBottom: 32,
                cursor: 'pointer',
            }} onClick={() => fileRef.current?.click()}>
                <input
                    ref={fileRef} type="file" accept=".pdf,.docx"
                    style={{ display: 'none' }} onChange={handleUpload}
                />
                {uploading ? (
                    <>
                        <div className="spinner" style={{ width: 40, height: 40, margin: '0 auto 16px' }} />
                        <p style={{ color: 'var(--text-secondary)' }}>Parsing your resume with AI...</p>
                    </>
                ) : (
                    <>
                        <Upload size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
                        <h3 style={{ marginBottom: 8 }}>Drop your resume here or click to upload</h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Supports PDF and DOCX files</p>
                    </>
                )}
            </div>

            {/* Resume list */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" /></div>
            ) : resumes.length === 0 ? (
                <div className="card empty-state">
                    <FileText size={64} />
                    <h3>No resumes yet</h3>
                    <p>Upload your first resume to get started</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {resumes.map(resume => (
                        <div key={resume.id} className="card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <div style={{
                                        width: 44, height: 44, borderRadius: 12,
                                        background: 'rgba(99,102,241,0.15)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    }}>
                                        <FileText size={22} color="#6366f1" />
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{resume.filename}</div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>
                                <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={() => setExpandedId(expandedId === resume.id ? null : resume.id)}
                                >
                                    {expandedId === resume.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                    Details
                                </button>
                            </div>

                            {expandedId === resume.id && (
                                <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border)' }}>
                                    {/* Skills */}
                                    {resume.parsed_json?.skills && resume.parsed_json.skills.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <h4 style={{ marginBottom: 8, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Skills</h4>
                                            <div className="tag-list">
                                                {resume.parsed_json.skills.map((s, i) => (
                                                    <span key={i} className="tag">{s}</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Experience */}
                                    {resume.parsed_json?.experience && resume.parsed_json.experience.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <h4 style={{ marginBottom: 8, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Experience</h4>
                                            {resume.parsed_json.experience.map((exp, i) => (
                                                <div key={i} style={{ marginBottom: 8 }}>
                                                    <span style={{ fontWeight: 600 }}>{exp.title}</span>
                                                    {exp.company && <span style={{ color: 'var(--text-muted)' }}> at {exp.company}</span>}
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* Raw text preview */}
                                    <div>
                                        <h4 style={{ marginBottom: 8, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Preview</h4>
                                        <pre style={{
                                            background: 'var(--bg-glass)', padding: 16, borderRadius: 8,
                                            fontSize: '0.8rem', maxHeight: 200, overflow: 'auto',
                                            whiteSpace: 'pre-wrap', color: 'var(--text-secondary)',
                                        }}>
                                            {resume.raw_text.substring(0, 1000)}
                                            {resume.raw_text.length > 1000 && '...'}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default ResumePage
