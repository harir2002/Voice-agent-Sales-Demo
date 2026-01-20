import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Phone,
    PhoneIncoming,
    PhoneOutgoing,
    Clock,
    TrendingUp,
    MessageSquare,
    Smile,
    Frown,
    Meh,
    CheckCircle,
    AlertCircle,
    XCircle,
    Search,
    Filter,
    RefreshCw,
    ChevronDown,
    ChevronUp,
    User,
    Bot,
    Calendar,
    BarChart3,
    Activity,
    Target,
    Users,
    ArrowUpRight,
    ArrowDownRight,
    Loader2
} from 'lucide-react'
import axios from 'axios'
import './CallDashboard.css'

const API_BASE_URL = 'https://voice-agent-sales-demo.onrender.com'

// Sentiment Icon Component
const SentimentIcon = ({ sentiment, size = 18 }) => {
    switch (sentiment?.toLowerCase()) {
        case 'positive':
            return <Smile size={size} className="sentiment-positive" />
        case 'negative':
            return <Frown size={size} className="sentiment-negative" />
        default:
            return <Meh size={size} className="sentiment-neutral" />
    }
}

// Outcome Badge Component
const OutcomeBadge = ({ outcome }) => {
    const getOutcomeStyle = () => {
        switch (outcome?.toLowerCase()) {
            case 'resolved':
                return { icon: <CheckCircle size={14} />, class: 'badge-success' }
            case 'escalated':
                return { icon: <AlertCircle size={14} />, class: 'badge-warning' }
            case 'callback_requested':
                return { icon: <Phone size={14} />, class: 'badge-info' }
            case 'abandoned':
                return { icon: <XCircle size={14} />, class: 'badge-danger' }
            default:
                return { icon: <Clock size={14} />, class: 'badge-default' }
        }
    }

    const { icon, class: badgeClass } = getOutcomeStyle()
    return (
        <span className={`outcome-badge ${badgeClass}`}>
            {icon}
            {outcome?.replace('_', ' ') || 'Unknown'}
        </span>
    )
}

// Metric Card Component
const MetricCard = ({ icon, title, value, subtitle, trend, trendValue, color }) => (
    <motion.div
        className={`metric-card metric-${color}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.02, y: -5 }}
    >
        <div className="metric-icon">{icon}</div>
        <div className="metric-content">
            <span className="metric-title">{title}</span>
            <span className="metric-value">{value}</span>
            {subtitle && <span className="metric-subtitle">{subtitle}</span>}
            {trend && (
                <span className={`metric-trend ${trend}`}>
                    {trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    {trendValue}
                </span>
            )}
        </div>
    </motion.div>
)

// Call Detail Modal Component
const CallDetailModal = ({ call, onClose }) => {
    if (!call) return null

    const formatDuration = (seconds) => {
        if (!seconds) return 'N/A'
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}m ${secs}s`
    }

    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleString('en-IN', {
            dateStyle: 'medium',
            timeStyle: 'short'
        })
    }

    return (
        <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
        >
            <motion.div
                className="call-detail-modal"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={e => e.stopPropagation()}
            >
                <div className="modal-header">
                    <div className="modal-title">
                        {call.call_type === 'inbound' ? (
                            <PhoneIncoming className="call-type-icon inbound" />
                        ) : (
                            <PhoneOutgoing className="call-type-icon outbound" />
                        )}
                        <h2>Call Details</h2>
                        <span className={`call-type-badge ${call.call_type}`}>
                            {call.call_type}
                        </span>
                    </div>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="modal-body">
                    {/* Call Info Grid */}
                    <div className="info-grid">
                        <div className="info-item">
                            <span className="info-label">Sector</span>
                            <span className="info-value">{call.sector}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">From</span>
                            <span className="info-value">{call.from_number}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">To</span>
                            <span className="info-value">{call.to_number}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Duration</span>
                            <span className="info-value">{formatDuration(call.duration_seconds)}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Started</span>
                            <span className="info-value">{formatDate(call.start_time)}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Outcome</span>
                            <OutcomeBadge outcome={call.outcome} />
                        </div>
                    </div>

                    {/* Sentiment Analysis */}
                    <div className="analysis-section">
                        <h3>
                            <SentimentIcon sentiment={call.overall_sentiment} size={20} />
                            Sentiment Analysis
                        </h3>
                        <div className="sentiment-breakdown">
                            <div className="sentiment-bar-container">
                                <div
                                    className="sentiment-bar positive"
                                    style={{ width: `${call.sentiment_breakdown?.positive || 0}%` }}
                                >
                                    {call.sentiment_breakdown?.positive > 10 && `${call.sentiment_breakdown?.positive}%`}
                                </div>
                                <div
                                    className="sentiment-bar neutral"
                                    style={{ width: `${call.sentiment_breakdown?.neutral || 0}%` }}
                                >
                                    {call.sentiment_breakdown?.neutral > 10 && `${call.sentiment_breakdown?.neutral}%`}
                                </div>
                                <div
                                    className="sentiment-bar negative"
                                    style={{ width: `${call.sentiment_breakdown?.negative || 0}%` }}
                                >
                                    {call.sentiment_breakdown?.negative > 10 && `${call.sentiment_breakdown?.negative}%`}
                                </div>
                            </div>
                            <div className="sentiment-legend">
                                <span className="legend-item positive">
                                    <Smile size={14} /> Positive
                                </span>
                                <span className="legend-item neutral">
                                    <Meh size={14} /> Neutral
                                </span>
                                <span className="legend-item negative">
                                    <Frown size={14} /> Negative
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Customer Intent */}
                    {call.customer_intent && (
                        <div className="analysis-section">
                            <h3><Target size={20} /> Customer Intent</h3>
                            <div className="intent-badge">{call.customer_intent}</div>
                            {call.topics_discussed?.length > 0 && (
                                <div className="topics-list">
                                    <span className="topics-label">Topics Discussed:</span>
                                    {call.topics_discussed.map((topic, idx) => (
                                        <span key={idx} className="topic-tag">{topic}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Performance Metrics */}
                    <div className="analysis-section">
                        <h3><Activity size={20} /> Performance Metrics</h3>
                        <div className="metrics-row">
                            <div className="metric-mini">
                                <span className="metric-mini-value">{call.avg_response_latency_ms || 'N/A'}ms</span>
                                <span className="metric-mini-label">Avg Response Latency</span>
                            </div>
                            <div className="metric-mini">
                                <span className="metric-mini-value">{call.total_agent_turns}</span>
                                <span className="metric-mini-label">Agent Turns</span>
                            </div>
                            <div className="metric-mini">
                                <span className="metric-mini-value">{call.total_customer_turns}</span>
                                <span className="metric-mini-label">Customer Turns</span>
                            </div>
                            <div className="metric-mini">
                                <span className={`metric-mini-value ${call.human_handoff_requested ? 'handoff' : ''}`}>
                                    {call.human_handoff_requested ? 'Yes' : 'No'}
                                </span>
                                <span className="metric-mini-label">Human Handoff</span>
                            </div>
                        </div>
                    </div>

                    {/* Transcription */}
                    {call.transcription?.length > 0 && (
                        <div className="transcription-section">
                            <h3><MessageSquare size={20} /> Full Transcription</h3>
                            <div className="transcription-container">
                                {call.transcription.map((turn, idx) => (
                                    <motion.div
                                        key={idx}
                                        className={`transcript-turn ${turn.speaker}`}
                                        initial={{ opacity: 0, x: turn.speaker === 'customer' ? -20 : 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                    >
                                        <div className="turn-header">
                                            <span className="turn-speaker">
                                                {turn.speaker === 'customer' ? (
                                                    <><User size={14} /> Customer</>
                                                ) : (
                                                    <><Bot size={14} /> AI Agent</>
                                                )}
                                            </span>
                                            <span className="turn-time">{turn.timestamp}</span>
                                            {turn.sentiment && <SentimentIcon sentiment={turn.sentiment} size={14} />}
                                            {turn.latency_ms && (
                                                <span className="turn-latency">{turn.latency_ms}ms</span>
                                            )}
                                        </div>
                                        <p className="turn-text">{turn.text}</p>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </motion.div>
        </motion.div>
    )
}

// Main Dashboard Component
function CallDashboard() {
    const [calls, setCalls] = useState([])
    const [summary, setSummary] = useState(null)
    const [realtimeMetrics, setRealtimeMetrics] = useState(null)
    const [loading, setLoading] = useState(true)
    const [selectedCall, setSelectedCall] = useState(null)
    const [expandedCallId, setExpandedCallId] = useState(null)
    const [analyticsStatus, setAnalyticsStatus] = useState(null)
    const [syncing, setSyncing] = useState(false)
    const [syncMessage, setSyncMessage] = useState('')

    // Filters
    const [filterType, setFilterType] = useState('all')
    const [filterSector, setFilterSector] = useState('all')
    const [filterSentiment, setFilterSentiment] = useState('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [showFilters, setShowFilters] = useState(false)

    const sectors = [
        { id: 'all', name: 'All Sectors' },
        { id: 'banking', name: 'Banking' },
        { id: 'financial', name: 'Financial Services' },
        { id: 'insurance', name: 'Insurance' },
        { id: 'bpo', name: 'BPO/Support' },
        { id: 'healthcare_appt', name: 'Healthcare (Appointments)' },
        { id: 'healthcare_patient', name: 'Healthcare (Patient)' }
    ]

    const fetchDashboardData = useCallback(async () => {
        try {
            setLoading(true)

            // Fetch calls
            const callParams = new URLSearchParams()
            if (filterType !== 'all') callParams.append('call_type', filterType)
            if (filterSector !== 'all') callParams.append('sector', filterSector)
            if (filterSentiment !== 'all') callParams.append('sentiment', filterSentiment)

            const [callsRes, summaryRes, realtimeRes, statusRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/analytics/calls?${callParams}`),
                axios.get(`${API_BASE_URL}/analytics/summary`),
                axios.get(`${API_BASE_URL}/analytics/metrics/realtime`),
                axios.get(`${API_BASE_URL}/analytics/status`)
            ])

            setCalls(callsRes.data)
            setSummary(summaryRes.data)
            setRealtimeMetrics(realtimeRes.data)
            setAnalyticsStatus(statusRes.data)
        } catch (error) {
            console.error('Error fetching dashboard data:', error)
        } finally {
            setLoading(false)
        }
    }, [filterType, filterSector, filterSentiment])

    const syncTwilioHistory = async () => {
        try {
            setSyncing(true)
            setSyncMessage('Syncing calls from Twilio...')
            const response = await axios.post(`${API_BASE_URL}/analytics/sync-twilio`)
            setSyncMessage(response.data.message)
            // Refresh data after sync
            await fetchDashboardData()
            setTimeout(() => setSyncMessage(''), 5000)
        } catch (error) {
            console.error('Sync error:', error)
            setSyncMessage(error.response?.data?.detail || 'Failed to sync. Is Twilio configured?')
            setTimeout(() => setSyncMessage(''), 5000)
        } finally {
            setSyncing(false)
        }
    }

    useEffect(() => {
        fetchDashboardData()

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchDashboardData, 30000)
        return () => clearInterval(interval)
    }, [fetchDashboardData])

    const formatDuration = (seconds) => {
        if (!seconds) return '0m 0s'
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}m ${secs}s`
    }

    const formatDate = (dateStr) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diffHours = Math.floor((now - date) / (1000 * 60 * 60))

        if (diffHours < 1) return 'Just now'
        if (diffHours < 24) return `${diffHours}h ago`
        return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
    }

    const filteredCalls = calls.filter(call => {
        if (searchQuery) {
            const query = searchQuery.toLowerCase()
            return (
                call.from_number?.toLowerCase().includes(query) ||
                call.to_number?.toLowerCase().includes(query) ||
                call.customer_intent?.toLowerCase().includes(query) ||
                call.sector?.toLowerCase().includes(query)
            )
        }
        return true
    })

    return (
        <div className="call-dashboard">
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-title">
                    <Phone size={32} className="header-icon" />
                    <div>
                        <h1>Call Analytics Dashboard</h1>
                        <p>
                            {analyticsStatus?.twilio_configured ? (
                                <span className="status-live">
                                    🟢 Live tracking active • {analyticsStatus.twilio_phone}
                                </span>
                            ) : (
                                <span className="status-offline">
                                    ⚪ Configure Twilio to enable live tracking
                                </span>
                            )}
                        </p>
                    </div>
                </div>
                <div className="header-actions">
                    {analyticsStatus?.twilio_configured && (
                        <button
                            className="sync-btn"
                            onClick={syncTwilioHistory}
                            disabled={syncing}
                        >
                            <RefreshCw size={18} className={syncing ? 'spin' : ''} />
                            {syncing ? 'Syncing...' : 'Sync Twilio History'}
                        </button>
                    )}
                    <button className="refresh-btn" onClick={fetchDashboardData} disabled={loading}>
                        <RefreshCw size={18} className={loading ? 'spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Sync Message */}
            {syncMessage && (
                <motion.div
                    className="sync-message"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                >
                    {syncMessage}
                </motion.div>
            )}

            {/* Metrics Overview */}
            <div className="metrics-overview">
                <MetricCard
                    icon={<Phone size={24} />}
                    title="Total Calls"
                    value={summary?.total_calls || 0}
                    subtitle={`${summary?.inbound_calls || 0} in / ${summary?.outbound_calls || 0} out`}
                    color="primary"
                />
                <MetricCard
                    icon={<Clock size={24} />}
                    title="Avg Duration"
                    value={formatDuration(summary?.avg_duration_seconds)}
                    color="blue"
                />
                <MetricCard
                    icon={<CheckCircle size={24} />}
                    title="Resolution Rate"
                    value={`${summary?.resolution_rate || 0}%`}
                    trend="up"
                    trendValue="+2.3%"
                    color="success"
                />
                <MetricCard
                    icon={<Users size={24} />}
                    title="Human Handoff"
                    value={`${summary?.human_handoff_rate || 0}%`}
                    trend="down"
                    trendValue="-1.5%"
                    color="warning"
                />
            </div>

            {/* Sentiment Distribution */}
            <div className="sentiment-overview">
                <h3><BarChart3 size={20} /> Sentiment Distribution</h3>
                <div className="sentiment-cards">
                    <div className="sentiment-card positive">
                        <Smile size={28} />
                        <span className="sentiment-count">{summary?.sentiment_distribution?.positive || 0}</span>
                        <span className="sentiment-label">Positive</span>
                    </div>
                    <div className="sentiment-card neutral">
                        <Meh size={28} />
                        <span className="sentiment-count">{summary?.sentiment_distribution?.neutral || 0}</span>
                        <span className="sentiment-label">Neutral</span>
                    </div>
                    <div className="sentiment-card negative">
                        <Frown size={28} />
                        <span className="sentiment-count">{summary?.sentiment_distribution?.negative || 0}</span>
                        <span className="sentiment-label">Negative</span>
                    </div>
                </div>
            </div>

            {/* Top Intents */}
            {summary?.top_intents?.length > 0 && (
                <div className="intents-section">
                    <h3><Target size={20} /> Top Customer Intents</h3>
                    <div className="intents-list">
                        {summary.top_intents.map((intent, idx) => (
                            <div key={idx} className="intent-item">
                                <span className="intent-rank">#{idx + 1}</span>
                                <span className="intent-name">{intent.intent}</span>
                                <div className="intent-bar">
                                    <div
                                        className="intent-fill"
                                        style={{ width: `${intent.percentage}%` }}
                                    />
                                </div>
                                <span className="intent-count">{intent.count} calls</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Filters & Search */}
            <div className="filters-section">
                <div className="search-box">
                    <Search size={18} />
                    <input
                        type="text"
                        placeholder="Search by phone, intent, sector..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <button
                    className={`filter-toggle ${showFilters ? 'active' : ''}`}
                    onClick={() => setShowFilters(!showFilters)}
                >
                    <Filter size={18} />
                    Filters
                    {showFilters ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                <AnimatePresence>
                    {showFilters && (
                        <motion.div
                            className="filters-panel"
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                        >
                            <div className="filter-group">
                                <label>Call Type</label>
                                <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                                    <option value="all">All Types</option>
                                    <option value="inbound">Inbound</option>
                                    <option value="outbound">Outbound</option>
                                </select>
                            </div>
                            <div className="filter-group">
                                <label>Sector</label>
                                <select value={filterSector} onChange={(e) => setFilterSector(e.target.value)}>
                                    {sectors.map(s => (
                                        <option key={s.id} value={s.id}>{s.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="filter-group">
                                <label>Sentiment</label>
                                <select value={filterSentiment} onChange={(e) => setFilterSentiment(e.target.value)}>
                                    <option value="all">All Sentiments</option>
                                    <option value="positive">Positive</option>
                                    <option value="neutral">Neutral</option>
                                    <option value="negative">Negative</option>
                                </select>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Call List */}
            <div className="calls-section">
                <h3>
                    <MessageSquare size={20} />
                    Recent Calls
                    <span className="call-count">{filteredCalls.length} calls</span>
                </h3>

                {loading ? (
                    <div className="loading-state">
                        <Loader2 size={32} className="spin" />
                        <p>Loading call data...</p>
                    </div>
                ) : filteredCalls.length === 0 ? (
                    <div className="empty-state">
                        <Phone size={48} />
                        <h4>No calls found</h4>
                        <p>Adjust your filters or wait for new calls</p>
                    </div>
                ) : (
                    <div className="calls-list">
                        {filteredCalls.map((call, index) => (
                            <motion.div
                                key={call.call_id}
                                className={`call-card ${expandedCallId === call.call_id ? 'expanded' : ''}`}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <div
                                    className="call-card-header"
                                    onClick={() => setExpandedCallId(
                                        expandedCallId === call.call_id ? null : call.call_id
                                    )}
                                >
                                    <div className="call-type-indicator">
                                        {call.call_type === 'inbound' ? (
                                            <PhoneIncoming className="inbound" size={20} />
                                        ) : (
                                            <PhoneOutgoing className="outbound" size={20} />
                                        )}
                                    </div>

                                    <div className="call-info">
                                        <div className="call-primary">
                                            <span className="call-number">
                                                {call.call_type === 'inbound' ? call.from_number : call.to_number}
                                            </span>
                                            <span className="call-sector">{call.sector}</span>
                                        </div>
                                        <div className="call-meta">
                                            <span className="call-time">
                                                <Calendar size={12} />
                                                {formatDate(call.start_time)}
                                            </span>
                                            <span className="call-duration">
                                                <Clock size={12} />
                                                {formatDuration(call.duration_seconds)}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="call-status">
                                        <SentimentIcon sentiment={call.overall_sentiment} size={22} />
                                        <OutcomeBadge outcome={call.outcome} />
                                    </div>

                                    <button
                                        className="expand-btn"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            setSelectedCall(call)
                                        }}
                                    >
                                        View Details
                                    </button>
                                </div>

                                <AnimatePresence>
                                    {expandedCallId === call.call_id && (
                                        <motion.div
                                            className="call-card-preview"
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                        >
                                            {call.customer_intent && (
                                                <div className="preview-item">
                                                    <strong>Intent:</strong> {call.customer_intent}
                                                </div>
                                            )}
                                            {call.transcription?.length > 0 && (
                                                <div className="preview-transcript">
                                                    <strong>Transcript Preview:</strong>
                                                    <p>"{call.transcription[0]?.text?.substring(0, 100)}..."</p>
                                                </div>
                                            )}
                                            <div className="preview-metrics">
                                                <span>Latency: {call.avg_response_latency_ms || 'N/A'}ms</span>
                                                <span>Turns: {call.total_agent_turns + call.total_customer_turns}</span>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>

            {/* Call Detail Modal */}
            <AnimatePresence>
                {selectedCall && (
                    <CallDetailModal
                        call={selectedCall}
                        onClose={() => setSelectedCall(null)}
                    />
                )}
            </AnimatePresence>
        </div>
    )
}

export default CallDashboard
