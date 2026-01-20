import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Phone, PhoneCall, PhoneOff, Settings, Check, X, Loader2 } from 'lucide-react'
import axios from 'axios'
import './TwilioDemo.css'

// Use environment variable for production, fallback to localhost for development
const API_BASE_URL = 'https://voice-agent-sales-demo.onrender.com'

function TwilioDemo() {
    // Configuration state
    const [isConfigured, setIsConfigured] = useState(false)
    const [showConfig, setShowConfig] = useState(false)
    const [configLoading, setConfigLoading] = useState(false)
    const [configError, setConfigError] = useState('')

    // Twilio credentials - Read from environment variables (set in Vercel dashboard)
    const [accountSid, setAccountSid] = useState(import.meta.env.VITE_TWILIO_ACCOUNT_SID || '')
    const [authToken, setAuthToken] = useState(import.meta.env.VITE_TWILIO_AUTH_TOKEN || '')
    const [phoneNumber, setPhoneNumber] = useState(import.meta.env.VITE_TWILIO_PHONE_NUMBER || '')
    const [webhookUrl, setWebhookUrl] = useState(import.meta.env.VITE_WEBHOOK_URL || '')

    // Call state
    const [activeTab, setActiveTab] = useState('inbound')
    const [outboundNumber, setOutboundNumber] = useState('')
    const [selectedSector, setSelectedSector] = useState('banking')
    const [callStatus, setCallStatus] = useState(null)
    const [callLoading, setCallLoading] = useState(false)
    const [activeCalls, setActiveCalls] = useState([])

    // Webhook configuration state
    const [webhookConfigured, setWebhookConfigured] = useState(false)
    const [webhookLoading, setWebhookLoading] = useState(false)
    const [webhookStatus, setWebhookStatus] = useState(null)
    const [inboundSector, setInboundSector] = useState('banking')

    // NEW: Outbound call purpose and customer name
    const [callPurpose, setCallPurpose] = useState('general')
    const [customerName, setCustomerName] = useState('')

    // Sectors for outbound calls
    const sectors = [
        { id: 'banking', name: 'Banking', icon: '🏦' },
        { id: 'financial', name: 'Financial Services', icon: '📈' },
        { id: 'insurance', name: 'Insurance', icon: '🛡️' },
        { id: 'bpo', name: 'BPO/Support', icon: '🎧' },
        { id: 'healthcare_appt', name: 'Healthcare (Appointments)', icon: '🗓️' },
        { id: 'healthcare_patient', name: 'Healthcare (Patient)', icon: '📋' }
    ]

    // Call purposes grouped by sector - for PROACTIVE outbound calls
    const callPurposes = {
        banking: [
            { id: 'general', name: '💬 General Inquiry' },
            { id: 'loan_reminder', name: '💰 EMI/Loan Reminder' },
            { id: 'payment_due', name: '💳 Payment Due Reminder' },
            { id: 'loan_offer', name: '🎁 Pre-approved Loan Offer' },
            { id: 'kyc_update', name: '📝 KYC Update Request' }
        ],
        financial: [
            { id: 'general', name: '💬 General Inquiry' },
            { id: 'investment_update', name: '📊 Portfolio Update' },
            { id: 'sip_reminder', name: '📅 SIP Payment Reminder' },
            { id: 'tax_saving', name: '🧾 Tax Saving Consultation' }
        ],
        insurance: [
            { id: 'general', name: '💬 General Inquiry' },
            { id: 'policy_renewal', name: '🔄 Policy Renewal Reminder' },
            { id: 'claim_status', name: '✅ Claim Status Update' },
            { id: 'premium_reminder', name: '💵 Premium Due Reminder' }
        ],
        bpo: [
            { id: 'general', name: '💬 General Inquiry' },
            { id: 'follow_up', name: '📞 Ticket Follow-up' },
            { id: 'feedback', name: '⭐ Feedback Request' },
            { id: 'subscription_expiry', name: '⏰ Subscription Renewal' }
        ],
        healthcare_appt: [
            { id: 'general', name: '💬 General Inquiry' },
            { id: 'appointment_confirmation', name: '📅 Appointment Confirmation' },
            { id: 'vaccination_reminder', name: '💉 Vaccination Reminder' },
            { id: 'checkup_reminder', name: '🩺 Health Checkup Reminder' }
        ],
        healthcare_patient: [
            { id: 'general', name: '💬 General Inquiry' },
            { id: 'lab_report_ready', name: '🔬 Lab Report Ready' },
            { id: 'checkup_reminder', name: '🩺 Health Checkup Reminder' }
        ]
    }

    // Check configuration on mount
    useEffect(() => {
        checkConfiguration()
    }, [])

    const checkConfiguration = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/twilio/config`)
            setIsConfigured(response.data.configured)
            if (response.data.phone_number) {
                setPhoneNumber(response.data.phone_number)
            }
            if (response.data.webhook_url) {
                setWebhookUrl(response.data.webhook_url)
            }
        } catch (error) {
            console.error('Error checking Twilio config:', error)
        }
    }

    const handleConfigure = async (e) => {
        e.preventDefault()
        setConfigLoading(true)
        setConfigError('')

        try {
            const response = await axios.post(`${API_BASE_URL}/twilio/configure`, {
                account_sid: accountSid,
                auth_token: authToken,
                phone_number: phoneNumber,
                webhook_url: webhookUrl
            })

            if (response.data.success) {
                setIsConfigured(true)
                setShowConfig(false)
                setConfigError('')
            }
        } catch (error) {
            setConfigError(error.response?.data?.detail || 'Failed to configure Twilio')
        } finally {
            setConfigLoading(false)
        }
    }

    const handleClearConfig = async () => {
        try {
            await axios.delete(`${API_BASE_URL}/twilio/config`)
            setIsConfigured(false)
            setAccountSid('')
            setAuthToken('')
            setPhoneNumber('')
            setWebhookUrl('')
        } catch (error) {
            console.error('Error clearing config:', error)
        }
    }

    const initiateOutboundCall = async () => {
        if (!outboundNumber.trim()) {
            setCallStatus({ type: 'error', message: 'Please enter a phone number' })
            return
        }

        setCallLoading(true)
        setCallStatus(null)

        try {
            const response = await axios.post(`${API_BASE_URL}/twilio/call/outbound`, {
                to_number: outboundNumber,
                sector: selectedSector,
                call_purpose: callPurpose,
                customer_name: customerName || 'valued customer'
            })

            if (response.data.success) {
                setCallStatus({
                    type: 'success',
                    message: `Call initiated! Call SID: ${response.data.call_sid}`,
                    callSid: response.data.call_sid
                })
                fetchActiveCalls()
            }
        } catch (error) {
            setCallStatus({
                type: 'error',
                message: error.response?.data?.detail || 'Failed to initiate call'
            })
        } finally {
            setCallLoading(false)
        }
    }

    const fetchActiveCalls = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/twilio/calls/active`)
            setActiveCalls(Object.entries(response.data.calls || {}))
        } catch (error) {
            console.error('Error fetching active calls:', error)
        }
    }

    const hangupCall = async (callSid) => {
        try {
            await axios.post(`${API_BASE_URL}/twilio/call/${callSid}/hangup`)
            fetchActiveCalls()
        } catch (error) {
            console.error('Error hanging up call:', error)
        }
    }

    // Configure webhook on Twilio phone number automatically
    const configureWebhook = async () => {
        setWebhookLoading(true)
        setWebhookStatus(null)

        try {
            const response = await axios.post(`${API_BASE_URL}/twilio/configure-webhook`, {
                sector: inboundSector
            })

            if (response.data.success) {
                setWebhookConfigured(true)
                setWebhookStatus({
                    type: 'success',
                    message: `✅ Webhook configured for ${inboundSector}! Inbound calls will now be handled by AI.`,
                    voiceUrl: response.data.voice_url
                })
            }
        } catch (error) {
            setWebhookStatus({
                type: 'error',
                message: error.response?.data?.detail || 'Failed to configure webhook'
            })
        } finally {
            setWebhookLoading(false)
        }
    }

    return (
        <div className="twilio-demo">
            <div className="twilio-header">
                <div className="twilio-logo">
                    <Phone size={32} />
                    <div>
                        <h2>Twilio Voice Integration</h2>
                        <p>Real Phone Call Demo with AI Voice Agent</p>
                    </div>
                </div>
                <button
                    className={`config-btn ${isConfigured ? 'configured' : ''}`}
                    onClick={() => setShowConfig(!showConfig)}
                >
                    <Settings size={18} />
                    {isConfigured ? 'Configured ✓' : 'Configure'}
                </button>
            </div>

            {/* Configuration Panel */}
            <AnimatePresence>
                {showConfig && (
                    <motion.div
                        className="config-panel"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                    >
                        <form onSubmit={handleConfigure}>
                            <h3>🔐 Twilio Credentials</h3>

                            <div className="form-grid">
                                <div className="form-group">
                                    <label>Account SID</label>
                                    <input
                                        type="text"
                                        value={accountSid}
                                        onChange={(e) => setAccountSid(e.target.value)}
                                        placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Auth Token</label>
                                    <input
                                        type="password"
                                        value={authToken}
                                        onChange={(e) => setAuthToken(e.target.value)}
                                        placeholder="Your auth token"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Twilio Phone Number</label>
                                    <input
                                        type="tel"
                                        value={phoneNumber}
                                        onChange={(e) => setPhoneNumber(e.target.value)}
                                        placeholder="+1234567890"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Webhook URL (ngrok or public URL)</label>
                                    <input
                                        type="url"
                                        value={webhookUrl}
                                        onChange={(e) => setWebhookUrl(e.target.value)}
                                        placeholder="https://your-ngrok-url.ngrok.io"
                                        required
                                    />
                                    <small>Run ngrok: ngrok http 8000</small>
                                </div>
                            </div>

                            {configError && (
                                <div className="error-message">{configError}</div>
                            )}

                            <div className="config-actions">
                                <button type="submit" className="save-btn" disabled={configLoading}>
                                    {configLoading ? <Loader2 className="spin" size={18} /> : <Check size={18} />}
                                    Save Configuration
                                </button>
                                {isConfigured && (
                                    <button type="button" className="clear-btn" onClick={handleClearConfig}>
                                        <X size={18} />
                                        Clear
                                    </button>
                                )}
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Demo Content */}
            {isConfigured ? (
                <div className="demo-content">
                    {/* Tab Selector */}
                    <div className="tab-selector">
                        <button
                            className={`tab ${activeTab === 'inbound' ? 'active' : ''}`}
                            onClick={() => setActiveTab('inbound')}
                        >
                            <PhoneCall size={20} />
                            Inbound Calls
                        </button>
                        <button
                            className={`tab ${activeTab === 'outbound' ? 'active' : ''}`}
                            onClick={() => setActiveTab('outbound')}
                        >
                            <Phone size={20} />
                            Outbound Calls
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="tab-content">
                        {activeTab === 'inbound' ? (
                            <div className="inbound-section">
                                <div className="call-info-card">
                                    <h3>📞 Inbound Call Demo</h3>
                                    <p>Customers can call this number to speak with our AI Voice Agent</p>

                                    <div className="phone-display">
                                        <span className="phone-label">Your Twilio Number</span>
                                        <span className="phone-number">{phoneNumber}</span>
                                    </div>

                                    {/* Webhook Configuration Section */}
                                    <div className="webhook-config-section">
                                        <h4>⚙️ Configure Webhook (One-Click Setup)</h4>
                                        <p>Select a sector and click the button to automatically configure your Twilio phone number to receive AI-powered calls.</p>

                                        <div className="inbound-sector-select">
                                            <label>Select Sector for Inbound Calls:</label>
                                            <select
                                                value={inboundSector}
                                                onChange={(e) => setInboundSector(e.target.value)}
                                                className="sector-dropdown"
                                            >
                                                {sectors.map(sector => (
                                                    <option key={sector.id} value={sector.id}>
                                                        {sector.icon} {sector.name}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        <button
                                            className="webhook-config-btn"
                                            onClick={configureWebhook}
                                            disabled={webhookLoading}
                                        >
                                            {webhookLoading ? (
                                                <Loader2 className="spin" size={18} />
                                            ) : (
                                                <Settings size={18} />
                                            )}
                                            Configure Webhook on Twilio
                                        </button>

                                        {webhookStatus && (
                                            <div className={`webhook-status ${webhookStatus.type}`}>
                                                {webhookStatus.message}
                                                {webhookStatus.voiceUrl && (
                                                    <div className="configured-url">
                                                        <small>Voice URL: {webhookStatus.voiceUrl}</small>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>

                                    <div className="test-call-info">
                                        <h4>📱 Test Your Setup</h4>
                                        <p>After configuring, call <strong>{phoneNumber}</strong> from any phone to test the AI voice agent!</p>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="outbound-section">
                                <div className="call-info-card">
                                    <h3>📤 Outbound Call Demo</h3>
                                    <p>AI agent initiates a call to a customer</p>

                                    <div className="outbound-form">
                                        <div className="form-group">
                                            <label>Customer Phone Number</label>
                                            <input
                                                type="tel"
                                                value={outboundNumber}
                                                onChange={(e) => setOutboundNumber(e.target.value)}
                                                placeholder="+91 98765 43210"
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label>Select Sector</label>
                                            <div className="sector-grid">
                                                {sectors.map(sector => (
                                                    <button
                                                        key={sector.id}
                                                        type="button"
                                                        className={`sector-btn ${selectedSector === sector.id ? 'active' : ''}`}
                                                        onClick={() => {
                                                            setSelectedSector(sector.id)
                                                            setCallPurpose('general') // Reset purpose when sector changes
                                                        }}
                                                    >
                                                        <span className="sector-icon">{sector.icon}</span>
                                                        <span className="sector-name">{sector.name}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* NEW: Customer Name Input */}
                                        <div className="form-group">
                                            <label>Customer Name (for personalized greeting)</label>
                                            <input
                                                type="text"
                                                value={customerName}
                                                onChange={(e) => setCustomerName(e.target.value)}
                                                placeholder="e.g., Rahul Kumar"
                                            />
                                        </div>

                                        {/* NEW: Call Purpose Selector */}
                                        <div className="form-group">
                                            <label>📢 Call Purpose (Proactive Script)</label>
                                            <select
                                                value={callPurpose}
                                                onChange={(e) => setCallPurpose(e.target.value)}
                                                className="purpose-dropdown"
                                            >
                                                {(callPurposes[selectedSector] || callPurposes.banking).map(purpose => (
                                                    <option key={purpose.id} value={purpose.id}>
                                                        {purpose.name}
                                                    </option>
                                                ))}
                                            </select>
                                            <small className="purpose-hint">
                                                {callPurpose !== 'general'
                                                    ? '✨ AI will proactively lead the conversation based on this purpose!'
                                                    : '💬 AI will wait for customer to ask questions (like inbound)'}
                                            </small>
                                        </div>

                                        <button
                                            className="call-btn"
                                            onClick={initiateOutboundCall}
                                            disabled={callLoading}
                                        >
                                            {callLoading ? (
                                                <Loader2 className="spin" size={20} />
                                            ) : (
                                                <PhoneCall size={20} />
                                            )}
                                            Initiate Call
                                        </button>

                                        {callStatus && (
                                            <div className={`call-status ${callStatus.type}`}>
                                                {callStatus.message}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Active Calls */}
                                {activeCalls.length > 0 && (
                                    <div className="active-calls">
                                        <h4>Active Calls</h4>
                                        {activeCalls.map(([callSid, call]) => (
                                            <div key={callSid} className="call-item">
                                                <div className="call-info">
                                                    <span className="call-type">{call.type}</span>
                                                    <span className="call-number">{call.to || call.from}</span>
                                                    <span className={`call-status-badge ${call.status}`}>
                                                        {call.status}
                                                    </span>
                                                </div>
                                                <button
                                                    className="hangup-btn"
                                                    onClick={() => hangupCall(callSid)}
                                                >
                                                    <PhoneOff size={16} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                <div className="not-configured">
                    <div className="setup-prompt">
                        <Phone size={64} />
                        <h3>Configure Twilio to Demo Real Phone Calls</h3>
                        <p>Add your Twilio credentials above to enable inbound and outbound voice calls with the AI agent.</p>
                        <button className="setup-btn" onClick={() => setShowConfig(true)}>
                            <Settings size={18} />
                            Setup Twilio
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default TwilioDemo
