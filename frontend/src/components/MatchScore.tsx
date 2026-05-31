/**
 * Circular score ring component — visual match score indicator.
 */

import React from 'react'

interface Props {
    score: number
    size?: number
    strokeWidth?: number
}

const MatchScore: React.FC<Props> = ({ score, size = 64, strokeWidth = 5 }) => {
    const radius = (size - strokeWidth) / 2
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (score / 100) * circumference

    const getColor = () => {
        if (score >= 80) return '#10b981'
        if (score >= 60) return '#6366f1'
        if (score >= 40) return '#f59e0b'
        return '#ef4444'
    }

    return (
        <div className="score-ring" style={{ width: size, height: size }}>
            <svg width={size} height={size}>
                <circle
                    cx={size / 2} cy={size / 2} r={radius}
                    fill="none"
                    stroke="rgba(255,255,255,0.06)"
                    strokeWidth={strokeWidth}
                />
                <circle
                    cx={size / 2} cy={size / 2} r={radius}
                    fill="none"
                    stroke={getColor()}
                    strokeWidth={strokeWidth}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 0.8s ease' }}
                />
            </svg>
            <span className="score-value" style={{ color: getColor() }}>
                {Math.round(score)}
            </span>
        </div>
    )
}

export default MatchScore
