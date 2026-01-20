import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight, Phone, BarChart3, Sparkles, Zap, Globe, Shield, HeadphonesIcon, TrendingUp, Clock, Users, Award, CheckCircle2, Calculator, Volume2 } from 'lucide-react'
import axios from 'axios'
import VoiceAgentPage from './VoiceAgentPage'
import TwilioDemo from './TwilioDemo'
import CallDashboard from './CallDashboard'
import CalculatorsSection from './CalculatorsSection'
import SarvamPlayground from './SarvamPlayground'
import './DemoPage.css'
import './CompanyStyles.css'

// Hardcoded backend URL for reliability
const API_BASE_URL = 'https://voice-agent-sales-demo.onrender.com'

// Hierarchical sector structure
const SECTOR_HIERARCHY = {
    bfsi: {
        id: 'bfsi',
        title: 'BFSI',
        fullName: 'Banking, Fintech/Financial Services & Insurance',
        icon: '💼',
        subSectors: ['banking', 'financial', 'insurance']
    },
    bpo: {
        id: 'bpo',
        title: 'BPO/KPO',
        fullName: 'Business Process Outsourcing',
        icon: '🎧',
        subSectors: ['bpo']
    },
    healthcare: {
        id: 'healthcare',
        title: 'Healthcare',
        fullName: 'Healthcare Services',
        icon: '🏥',
        subSectors: ['healthcare_appt', 'healthcare_patient']
    }
}

// Stats data for dashboard
const STATS = [
    { icon: Clock, value: '<2s', label: 'Response Time', color: '#10b981' },
    { icon: Users, value: '8+', label: 'Indian Languages', color: '#3b82f6' },
    { icon: TrendingUp, value: '24/7', label: 'Availability', color: '#f59e0b' },
    { icon: Award, value: '100%', label: 'Customizable', color: '#ec4899' }
]

// Key Features for Hero
const KEY_FEATURES = [
    {
        icon: Zap,
        title: 'Lightning Fast',
        desc: 'Sub-2 second latency',
        color: '#f59e0b'
    },
    {
        icon: Globe,
        title: 'Multi-lingual',
        desc: '8 Indian languages',
        color: '#3b82f6'
    },
    {
        icon: HeadphonesIcon,
        title: 'Human Handoff',
        desc: 'Seamless escalation',
        color: '#10b981'
    },
    {
        icon: Shield,
        title: 'Enterprise Ready',
        desc: 'SOC2 compliant',
        color: '#8b5cf6'
    }
]

// Core Capabilities
const CAPABILITIES = [
    {
        category: 'Unique Differentiators',
        icon: '🚀',
        items: [
            { icon: '🛑', title: 'Interruption Handling', desc: 'Interrupt the AI anytime - like a real human conversation', tag: 'Industry First', highlight: true },
            { icon: '🔄', title: 'Context Switching', desc: 'Switch topics mid-conversation without losing memory', tag: 'Smart Memory', highlight: true },
            { icon: '⚡', title: 'Sub-2s Latency', desc: 'Ultra-fast responses with intelligent caching', tag: 'Lightning Fast', highlight: true },
            { icon: '🧠', title: 'Human Handoff', desc: 'Automatic escalation to live agents when needed', tag: 'Smart Routing', highlight: false }
        ]
    },
    {
        category: 'Multi-Language Excellence',
        icon: '🌐',
        items: [
            { icon: '🗣️', title: '8 Indian Languages', desc: 'Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi + English', tag: 'Regional' },
            { icon: '🇮🇳', title: 'Indian Accent Recognition', desc: 'Optimized for Indian English and Hinglish code-switching', tag: 'Native Feel' },
            { icon: '✍️', title: 'Live Transcription', desc: 'Real-time speech-to-text with instant feedback', tag: 'Accessibility' },
            { icon: '🎙️', title: 'Sector-Specific Voices', desc: 'Custom voice personas for each industry', tag: 'Brand Identity' }
        ]
    },
    {
        category: 'Enterprise Technology',
        icon: '⚙️',
        items: [
            { icon: '📚', title: 'RAG Knowledge Base', desc: 'Domain-specific knowledge for accurate answers', tag: 'Accuracy' },
            { icon: '🔐', title: 'Enterprise Security', desc: 'Data encryption, secure APIs, and role-based access control', tag: 'Secure' },
            { icon: '📊', title: 'Analytics Dashboard', desc: 'Real-time metrics and call insights', tag: 'Insights' },
            { icon: '🔗', title: 'Easy Integration', desc: 'REST APIs and CRM connectors', tag: 'Plug & Play' }
        ]
    }
]

function DemoPage() {
    const [sectors, setSectors] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [expandedCategory, setExpandedCategory] = useState(null)
    const [selectedSector, setSelectedSector] = useState(null)
    const [showTwilioDemo, setShowTwilioDemo] = useState(false)
    const [showDashboard, setShowDashboard] = useState(false)
    const [showCalculators, setShowCalculators] = useState(false)
    const [showPlayground, setShowPlayground] = useState(false)
    const [activeCapabilityTab, setActiveCapabilityTab] = useState(0)

    useEffect(() => {
        fetchSectors()
    }, [])

    const fetchSectors = async () => {
        try {
            console.log('Fetching sectors from:', `${API_BASE_URL}/sectors`)
            const response = await axios.get(`${API_BASE_URL}/sectors`)
            console.log('Sectors fetched:', response.data)
            setSectors(response.data)
            setError(null)
        } catch (error) {
            console.error('Error fetching sectors:', error)
            setError(`Failed to load sectors: ${error.message}`)
        } finally {
            setLoading(false)
        }
    }

    const toggleCategory = (categoryId) => {
        setExpandedCategory(expandedCategory === categoryId ? null : categoryId)
    }

    const getSectorsByCategory = (categoryId) => {
        const category = SECTOR_HIERARCHY[categoryId]
        if (!sectors || sectors.length === 0) return []
        return sectors.filter(sector => category.subSectors.includes(sector.id))
    }

    const handleSectorSelect = (sector) => {
        setSelectedSector(sector)
        setShowTwilioDemo(false)
        setShowDashboard(false)
        setShowCalculators(false)
    }

    const goHome = () => {
        setSelectedSector(null)
        setShowTwilioDemo(false)
        setShowDashboard(false)
        setShowCalculators(false)
        setShowPlayground(false)
    }

    return (
        <div className="demo-page">
            {/* Left Sidebar */}
            <motion.div
                className="sidebar"
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
            >
                <div className="sidebar-header">
                    {(selectedSector || showTwilioDemo || showDashboard || showCalculators || showPlayground) && (
                        <button className="back-home-btn" onClick={goHome}>
                            ← Back to Home
                        </button>
                    )}
                    <div className="logo-wrapper">
                        <img src="/logo.png" alt="SBA Logo" className="sidebar-logo" />
                    </div>
                    <h2 className="sidebar-title gradient-text">AI Voice Agents</h2>
                    <p className="sidebar-subtitle">Select a sector to demo</p>
                </div>

                <div className="sectors-list">
                    {error && (
                        <div style={{ color: '#ff4d4d', fontSize: '0.8rem', padding: '0.5rem', textAlign: 'center', background: 'rgba(231,0,11,0.1)', borderRadius: '4px', margin: '0.5rem 0' }}>
                            ⚠️ {error}
                        </div>
                    )}

                    {loading ? (
                        <div className="loading">Loading sectors...</div>
                    ) : (
                        Object.values(SECTOR_HIERARCHY).map((category, index) => (
                            <motion.div
                                key={category.id}
                                className="category-container"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                            >
                                <motion.div
                                    className={`category-header ${expandedCategory === category.id ? 'expanded' : ''}`}
                                    onClick={() => toggleCategory(category.id)}
                                    whileHover={{ x: 5 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    <div className="category-icon">{category.icon}</div>
                                    <div className="category-info">
                                        <h3 className="category-title">{category.title}</h3>
                                        <p className="category-subtitle">{category.fullName}</p>
                                    </div>
                                    <motion.div
                                        className="category-chevron"
                                        animate={{ rotate: expandedCategory === category.id ? 180 : 0 }}
                                        transition={{ duration: 0.3 }}
                                    >
                                        <ChevronDown size={20} />
                                    </motion.div>
                                </motion.div>

                                <AnimatePresence>
                                    {expandedCategory === category.id && (
                                        <motion.div
                                            className="subsectors-container"
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.3 }}
                                        >
                                            {getSectorsByCategory(category.id).length > 0 ? (
                                                getSectorsByCategory(category.id).map((sector, subIndex) => (
                                                    <motion.div
                                                        key={sector.id}
                                                        className={`subsector-card ${selectedSector?.id === sector.id ? 'active' : ''}`}
                                                        onClick={() => handleSectorSelect(sector)}
                                                        initial={{ opacity: 0, x: -10 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        transition={{ delay: subIndex * 0.05 }}
                                                        whileHover={{ x: 5 }}
                                                        whileTap={{ scale: 0.97 }}
                                                    >
                                                        <div className="subsector-icon">{sector.icon}</div>
                                                        <div className="subsector-info">
                                                            <h4 className="subsector-title">{sector.title}</h4>
                                                            <p className="subsector-subtitle">{sector.subtitle}</p>
                                                        </div>
                                                        <ChevronRight className="subsector-arrow" size={16} />
                                                    </motion.div>
                                                ))
                                            ) : (
                                                <div style={{ padding: '1rem', color: '#999', fontSize: '0.8rem', textAlign: 'center' }}>
                                                    {sectors.length === 0 ? "No data loaded." : "No sub-sectors found."}
                                                </div>
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        ))
                    )}

                    {/* Separator */}
                    <div className="sidebar-separator">
                        <span>Quick Actions</span>
                    </div>

                    {/* Twilio Phone Calls Section */}
                    <motion.div
                        className="category-container twilio-section"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                    >
                        <motion.div
                            className={`category-header quickaction ${showTwilioDemo ? 'expanded' : ''}`}
                            onClick={() => {
                                setShowTwilioDemo(true)
                                setSelectedSector(null)
                                setShowDashboard(false)
                                setShowCalculators(false)
                            }}
                            whileHover={{ x: 5 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <div className="category-icon-wrapper phone">
                                <Phone size={22} />
                            </div>
                            <div className="category-info">
                                <h3 className="category-title">Phone Calls</h3>
                                <p className="category-subtitle">Inbound & Outbound Voice</p>
                            </div>
                        </motion.div>
                    </motion.div>

                    {/* Call Analytics Dashboard Section */}
                    <motion.div
                        className="category-container dashboard-section"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                    >
                        <motion.div
                            className={`category-header quickaction ${showDashboard ? 'expanded' : ''}`}
                            onClick={() => {
                                setShowDashboard(true)
                                setSelectedSector(null)
                                setShowTwilioDemo(false)
                                setShowCalculators(false)
                            }}
                            whileHover={{ x: 5 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <div className="category-icon-wrapper analytics">
                                <BarChart3 size={22} />
                            </div>
                            <div className="category-info">
                                <h3 className="category-title">Analytics</h3>
                                <p className="category-subtitle">Dashboard & Insights</p>
                            </div>
                        </motion.div>
                    </motion.div>

                    {/* ROI Calculators Section */}
                    <motion.div
                        className="category-container calculators-section-sidebar"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 }}
                    >
                        <motion.div
                            className={`category-header quickaction ${showCalculators ? 'expanded' : ''}`}
                            onClick={() => {
                                setShowCalculators(true)
                                setSelectedSector(null)
                                setShowTwilioDemo(false)
                                setShowDashboard(false)
                            }}
                            whileHover={{ x: 5 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <div className="category-icon-wrapper calculator">
                                <Calculator size={22} />
                            </div>
                            <div className="category-info">
                                <h3 className="category-title">ROI Calculators</h3>
                                <p className="category-subtitle">Financial Analysis Tools</p>
                            </div>
                        </motion.div>
                    </motion.div>

                    {/* Sarvam TTS Playground Section */}
                    <motion.div
                        className="category-container playground-section"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.7 }}
                    >
                        <motion.div
                            className={`category-header quickaction ${showPlayground ? 'expanded' : ''}`}
                            onClick={() => {
                                setShowPlayground(true)
                                setSelectedSector(null)
                                setShowTwilioDemo(false)
                                setShowDashboard(false)
                                setShowCalculators(false)
                            }}
                            whileHover={{ x: 5 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <div className="category-icon-wrapper voice">
                                <Volume2 size={22} />
                            </div>
                            <div className="category-info">
                                <h3 className="category-title">TTS Playground</h3>
                                <p className="category-subtitle">Test Sarvam Voices</p>
                            </div>
                        </motion.div>
                    </motion.div>
                </div>

                <div className="sidebar-footer">
                    <p className="company-name">SBA Info Solutions Pvt Ltd</p>
                    <p className="company-ref">Enterprise AI Solutions</p>
                </div>
            </motion.div>

            {/* Right Content Area */}
            <div className="demo-content">
                <AnimatePresence mode="wait">
                    {showDashboard ? (
                        <motion.div
                            key="dashboard"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="demo-content-wrapper"
                        >
                            <CallDashboard />
                        </motion.div>
                    ) : showTwilioDemo ? (
                        <motion.div
                            key="twilio"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="demo-content-wrapper"
                        >
                            <TwilioDemo />
                        </motion.div>
                    ) : selectedSector ? (
                        <motion.div
                            key={selectedSector.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="demo-content-wrapper"
                        >
                            <VoiceAgentPage sector={selectedSector} onBack={null} />
                        </motion.div>
                    ) : showCalculators ? (
                        <motion.div
                            key="calculators"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="demo-content-wrapper calculators-page"
                        >
                            <CalculatorsSection />
                        </motion.div>
                    ) : showPlayground ? (
                        <motion.div
                            key="playground"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="demo-content-wrapper"
                        >
                            <SarvamPlayground />
                        </motion.div>
                    ) : (
                        <motion.div
                            key="empty"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="hero-landing"
                        >
                            {/* Hero Section */}
                            <section className="hero-section-new">
                                <motion.div
                                    className="hero-brand-container"
                                    initial={{ opacity: 0, y: -30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6 }}
                                >
                                    <div className="hero-logo-glow">
                                        <img src="/logo.png" alt="SBA Info Solutions" className="hero-main-logo" />
                                    </div>
                                    <div className="hero-text-block">
                                        <h1 className="hero-main-title">
                                            Next-Gen <span className="text-gradient">AI Voice Agents</span>
                                        </h1>
                                        <p className="hero-main-subtitle">
                                            Transform your customer experience with intelligent, human-like voice interactions
                                        </p>
                                    </div>
                                </motion.div>
                            </section>

                            {/* Capabilities Section with Tabs - MOVED UP */}
                            <section className="capabilities-section capabilities-top">
                                <motion.div
                                    className="section-header"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.3 }}
                                >
                                    <Sparkles className="section-icon" />
                                    <h2>Why Choose Our AI Voice Agent?</h2>
                                </motion.div>

                                {/* Capability Tabs */}
                                <motion.div
                                    className="capability-tabs"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: 0.4 }}
                                >
                                    {CAPABILITIES.map((cap, index) => (
                                        <motion.button
                                            key={index}
                                            className={`capability-tab ${activeCapabilityTab === index ? 'active' : ''}`}
                                            onClick={() => setActiveCapabilityTab(index)}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                        >
                                            <span className="tab-icon">{cap.icon}</span>
                                            <span>{cap.category}</span>
                                        </motion.button>
                                    ))}
                                </motion.div>

                                {/* Active Capability Content */}
                                <AnimatePresence mode="wait">
                                    <motion.div
                                        key={activeCapabilityTab}
                                        className="capability-content"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -20 }}
                                        transition={{ duration: 0.3 }}
                                    >
                                        <div className="capability-grid-new">
                                            {CAPABILITIES[activeCapabilityTab].items.map((item, index) => (
                                                <motion.div
                                                    key={index}
                                                    className={`capability-card-new ${item.highlight ? 'highlight' : ''}`}
                                                    initial={{ opacity: 0, y: 20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    transition={{ delay: index * 0.08 }}
                                                    whileHover={{ y: -8, boxShadow: '0 20px 50px rgba(231, 0, 11, 0.25)' }}
                                                >
                                                    <div className="card-top">
                                                        <span className="cap-icon">{item.icon}</span>
                                                        {item.highlight && <CheckCircle2 className="highlight-badge" size={18} />}
                                                    </div>
                                                    <h4>{item.title}</h4>
                                                    <p>{item.desc}</p>
                                                    <span className="cap-tag">{item.tag}</span>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </motion.div>
                                </AnimatePresence>
                            </section>

                            {/* Quick Stats Bar */}
                            <section className="stats-section">
                                <motion.div
                                    className="stats-bar"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6, delay: 0.5 }}
                                >
                                    {STATS.map((stat, index) => (
                                        <motion.div
                                            key={index}
                                            className="stat-item"
                                            initial={{ opacity: 0, scale: 0.8 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            transition={{ delay: 0.6 + index * 0.1 }}
                                            whileHover={{ scale: 1.05, y: -3 }}
                                        >
                                            <stat.icon className="stat-icon" style={{ color: stat.color }} size={24} />
                                            <span className="stat-value" style={{ color: stat.color }}>{stat.value}</span>
                                            <span className="stat-label">{stat.label}</span>
                                        </motion.div>
                                    ))}
                                </motion.div>
                            </section>

                            {/* Key Features Quick View */}
                            <section className="features-section">
                                <motion.div
                                    className="quick-features"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ duration: 0.6, delay: 0.7 }}
                                >
                                    {KEY_FEATURES.map((feature, index) => (
                                        <motion.div
                                            key={index}
                                            className="quick-feature-card"
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.8 + index * 0.1 }}
                                            whileHover={{ scale: 1.03, y: -5 }}
                                        >
                                            <div className="quick-feature-icon" style={{ background: `${feature.color}20`, color: feature.color }}>
                                                <feature.icon size={24} />
                                            </div>
                                            <div className="quick-feature-text">
                                                <h4>{feature.title}</h4>
                                                <p>{feature.desc}</p>
                                            </div>
                                        </motion.div>
                                    ))}
                                </motion.div>
                            </section>

                            {/* CTA Section */}
                            <motion.section
                                className="cta-section-new"
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.8 }}
                            >
                                <div className="cta-content">
                                    <div className="cta-icon-pulse">
                                        <span>👈</span>
                                    </div>
                                    <div className="cta-text-block">
                                        <h3>Ready to Experience the Future?</h3>
                                        <p>Select a sector from the sidebar to start your interactive demo</p>
                                    </div>
                                </div>
                                <div className="cta-decorative">
                                    <div className="pulse-ring ring1"></div>
                                    <div className="pulse-ring ring2"></div>
                                    <div className="pulse-ring ring3"></div>
                                </div>
                            </motion.section>

                            {/* Footer Trust Badges */}
                            <motion.section
                                className="trust-section"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 1 }}
                            >
                                <div className="trust-badges">
                                    <span className="trust-badge">🔒 Secure & Encrypted</span>
                                    <span className="trust-badge">🏆 Enterprise Ready</span>
                                    <span className="trust-badge">⚡ High Availability</span>
                                    <span className="trust-badge">🇮🇳 Made in India</span>
                                </div>
                            </motion.section>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}

export default DemoPage
