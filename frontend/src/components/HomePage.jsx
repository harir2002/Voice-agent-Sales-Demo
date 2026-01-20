import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight } from 'lucide-react'
import axios from 'axios'
import './HomePage.css'
import './CompanyStyles.css'

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

function HomePage({ onSectorSelect }) {
    const [loading, setLoading] = useState(true)
    const [expandedCategory, setExpandedCategory] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchSectors()
    }, [])

    const fetchSectors = async () => {
        try {
            console.log('Fetching from:', `${API_BASE_URL}/sectors`)
            const response = await axios.get(`${API_BASE_URL}/sectors`)
            setSectors(response.data)
            setError(null)
        } catch (error) {
            console.error('Error fetching sectors:', error)
            setError(`Failed to load sectors (${error.message}). API: ${API_BASE_URL}`)
        } finally {
            setLoading(false)
        }
    }

    const toggleCategory = (categoryId) => {
        console.log(`Toggling category: ${categoryId}. Current expanded: ${expandedCategory}`)
        setExpandedCategory(expandedCategory === categoryId ? null : categoryId)
    }

    const getSectorsByCategory = (categoryId) => {
        const category = SECTOR_HIERARCHY[categoryId]
        if (!sectors || sectors.length === 0) {
            console.warn("No sectors available to filter")
            return []
        }
        const filtered = sectors.filter(sector => category.subSectors.includes(sector.id))
        console.log(`Category ${categoryId} has ${filtered.length} sectors`)
        return filtered
    }

    // Debugging: Log sectors when they change
    useEffect(() => {
        console.log('Sectors state updated:', sectors)
    }, [sectors])

    return (
        <div className="home-page">
            <motion.div
                className="hero-section"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
            >
                <div className="logo-wrapper">
                    <img src="/logo.png" alt="SBA Logo" className="hero-logo" />
                    <p className="company-name">SBA Info Solutions Private Limited</p>
                </div>

                <h1 className="hero-title gradient-text">
                    Sector-Based AI Agents
                </h1>
                <p className="hero-subtitle">
                    Experience intelligent voice conversations powered by advanced AI
                </p>

                {/* 🎯 Key Features Showcase */}
                <motion.div
                    className="features-showcase"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.6 }}
                >
                    <div className="feature-card">
                        <div className="feature-icon">🛑</div>
                        <h3 className="feature-title">Interruption Handling</h3>
                        <p className="feature-desc">Interrupt the AI anytime while it's speaking - just like a real conversation</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">🔄</div>
                        <h3 className="feature-title">Context Switching</h3>
                        <p className="feature-desc">Seamlessly switch topics mid-conversation without losing context</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">⚡</div>
                        <h3 className="feature-title">Real-Time Response</h3>
                        <p className="feature-desc">Sub-2 second latency with intelligent caching and optimization</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">🎤</div>
                        <h3 className="feature-title">Natural Voice</h3>
                        <p className="feature-desc">Sector-specific voices with auto-detection and live transcription</p>
                    </div>
                </motion.div>
            </motion.div>

            <motion.div
                className="sectors-hierarchy"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
            >
                {error && (
                    <div style={{ color: '#ff4d4d', textAlign: 'center', padding: '1rem', background: 'rgba(231,0,11,0.1)', borderRadius: '8px', marginBottom: '1rem' }}>
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
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <motion.div
                                className="category-header"
                                onClick={() => toggleCategory(category.id)}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                style={{ background: category.gradient }}
                            >
                                <div className="category-icon">{category.icon}</div>
                                <div className="category-info">
                                    <h2 className="category-title">{category.title}</h2>
                                    <p className="category-subtitle">{category.fullName}</p>
                                </div>
                                <motion.div
                                    className="category-chevron"
                                    animate={{ rotate: expandedCategory === category.id ? 180 : 0 }}
                                    transition={{ duration: 0.3 }}
                                >
                                    <ChevronDown size={24} />
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
                                                    className="subsector-card glassmorphism"
                                                    onClick={() => onSectorSelect(sector)}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: subIndex * 0.05 }}
                                                    whileHover={{ scale: 1.03, x: 10 }}
                                                    whileTap={{ scale: 0.97 }}
                                                >
                                                    <div className="subsector-icon">{sector.icon}</div>
                                                    <div className="subsector-info">
                                                        <h3 className="subsector-title">{sector.title}</h3>
                                                        <p className="subsector-subtitle">{sector.subtitle}</p>
                                                        <div className="subsector-tags">{sector.tags}</div>
                                                    </div>
                                                    <ChevronRight className="subsector-arrow" size={20} />
                                                </motion.div>
                                            ))
                                        ) : (
                                            <div style={{ padding: '1rem', color: '#ccc', textAlign: 'center' }}>
                                                {sectors.length === 0 ? "Loading data or API error..." : "No sectors found for this category."}
                                            </div>
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    ))
                )}
            </motion.div>
        </div>
    )
}

export default HomePage
