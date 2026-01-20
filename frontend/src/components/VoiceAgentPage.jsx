import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Mic, Send, Trash2, Volume2 } from 'lucide-react'
import axios from 'axios'
import './VoiceAgentPage.css'
import './CompanyStyles.css'

const API_BASE_URL = 'https://voice-agent-sales-demo.onrender.com'

function VoiceAgentPage({ sector, onBack }) {
    const [messages, setMessages] = useState([])
    const [isRecording, setIsRecording] = useState(false)
    const [isProcessing, setIsProcessing] = useState(false)
    const [textInput, setTextInput] = useState('')
    const [transcriptionPreview, setTranscriptionPreview] = useState('')
    const [currentAudio, setCurrentAudio] = useState(null)
    const [welcomePlayed, setWelcomePlayed] = useState(false)
    const [isAISpeaking, setIsAISpeaking] = useState(false) // Track if AI is currently speaking
    const [selectedLanguage, setSelectedLanguage] = useState('en') // Language selection
    const [needsHumanHandoff, setNeedsHumanHandoff] = useState(false) // Human handoff flag
    const [callMode, setCallMode] = useState(true) // Phone call mode - auto-restart mic after AI speaks
    const [sampleLangTab, setSampleLangTab] = useState('english') // Sample questions language tab

    const recognitionRef = useRef(null)
    const messagesContainerRef = useRef(null)
    const silenceTimerRef = useRef(null)
    const transcriptionRef = useRef('') // Track latest transcript for closure access
    const fillerTimerRef = useRef(null) // Track filler timer for cleanup
    const isFillerPlayingRef = useRef(false) // Track if filler is currently playing
    const fillerCancelledRef = useRef(false) // Flag to cancel filler before it plays

    useEffect(() => {
        // Scroll container to bottom when messages change
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
        }
    }, [messages])

    // Auto-play welcome message when page loads
    useEffect(() => {
        if (!welcomePlayed) {
            playWelcomeMessage()
            setWelcomePlayed(true)
        }
    }, [welcomePlayed])

    const playWelcomeMessage = async () => {
        const welcomeMessages = {
            banking: "Hello! Welcome to our Banking Services. I'm your virtual banking assistant. How may I help you today?",
            financial: "Good day! Welcome to Fintech and Financial Services. I'm here to assist you with digital payments, investments, and wealth management. How can I help?",
            insurance: "Hello! Welcome to Insurance Services. I'm your virtual insurance assistant, ready to help with your policy and claims. What can I do for you?",
            bpo: "Hello! Welcome to Customer Support. I'm your virtual support agent. How may I assist you today?",
            healthcare_appt: "Good day! Welcome to Healthcare Appointment Services. I'm here to help you schedule and manage appointments. How can I assist you?",
            healthcare_patient: "Hello! Welcome to Patient Support Services. I'm your virtual healthcare assistant. How may I help you today?"
        }

        const welcomeText = welcomeMessages[sector.id] || "Hello! How may I help you today?"

        try {
            const timestamp = new Date().toISOString()
            setMessages([{
                type: 'ai',
                text: welcomeText,
                timestamp: timestamp
            }])

            const ttsResponse = await axios.post(`${API_BASE_URL}/tts`, {
                text: welcomeText,
                sector: sector.id
            })

            if (ttsResponse.data.audio) {
                setMessages([{
                    type: 'ai',
                    text: welcomeText,
                    audio: ttsResponse.data.audio,
                    timestamp: timestamp
                }])

                // 🎯 Enable interruption for welcome message
                setIsAISpeaking(true)

                // Start recording before playing audio to allow interruption
                setTimeout(() => {
                    startRecording()
                }, 100)

                // Play welcome message
                playAudioResponse(ttsResponse.data.audio, () => {
                    console.log("Welcome message ended - auto-starting mic")
                    setIsAISpeaking(false)
                    // Auto-restart mic for continuous conversation
                    setTimeout(() => {
                        startRecording()
                        console.log('🎤 Mic ready for next question')
                    }, 300)
                })
            } else {
                startRecording()
            }
        } catch (error) {
            console.error('Error playing welcome message:', error)
            startRecording()
        }
    }

    useEffect(() => {
        // Initialize Web Speech API
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
            recognitionRef.current = new SpeechRecognition()
            recognitionRef.current.continuous = true
            recognitionRef.current.interimResults = true
            // Support for Indian accents - use Indian English
            recognitionRef.current.lang = selectedLanguage === 'hi' ? 'hi-IN' :
                selectedLanguage === 'ta' ? 'ta-IN' :
                    selectedLanguage === 'te' ? 'te-IN' :
                        selectedLanguage === 'kn' ? 'kn-IN' :
                            selectedLanguage === 'ml' ? 'ml-IN' :
                                selectedLanguage === 'bn' ? 'bn-IN' :
                                    selectedLanguage === 'mr' ? 'mr-IN' : 'en-IN' // Default to Indian English

            recognitionRef.current.onresult = (event) => {
                let finalTranscript = ''
                let interimTranscript = ''

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    const transcript = event.results[i][0].transcript
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript
                    } else {
                        interimTranscript += transcript
                    }
                }

                const currentTranscript = finalTranscript + interimTranscript
                setTranscriptionPreview(currentTranscript)
                transcriptionRef.current = currentTranscript // Update ref

                // 🎯 INTERRUPTION HANDLING: If AI is speaking and user starts talking, stop AI immediately
                if (isAISpeaking && currentTranscript.trim().length > 3) {
                    console.log('🛑 User interrupted AI! Stopping audio...')
                    handleInterruption()
                }

                // Clear existing silence timer
                if (silenceTimerRef.current) {
                    clearTimeout(silenceTimerRef.current)
                }

                // Auto-submit after 1.2 seconds of silence (increased for multilingual support)
                if (currentTranscript.trim()) {
                    silenceTimerRef.current = setTimeout(() => {
                        console.log('✅ Auto-submitting after silence...')
                        stopRecording()
                    }, 1200)
                }
            }

            recognitionRef.current.onerror = (event) => {
                console.error('Speech recognition error', event.error)
                setIsRecording(false)
            }

            recognitionRef.current.onend = () => {
                if (silenceTimerRef.current) {
                    clearTimeout(silenceTimerRef.current)
                }
                setIsRecording(false)

                // Auto-restart if not processing and call mode is on
                // This handles cases where recognition ends unexpectedly
                if (callMode && !isProcessing && !isAISpeaking) {
                    console.log('🎤 Recognition ended - Auto-restarting mic')
                    setTimeout(() => {
                        if (!isProcessing && !isAISpeaking) {
                            startRecording()
                        }
                    }, 500)
                }
            }
        } else {
            alert('Web Speech API is not supported. Please use Chrome.')
        }

        return () => {
            if (silenceTimerRef.current) {
                clearTimeout(silenceTimerRef.current)
            }
            if (recognitionRef.current) {
                recognitionRef.current.abort() // abort() is more immediate than stop()
            }
        }
    }, [])

    // Cleanup audio on unmount
    useEffect(() => {
        return () => {
            if (currentAudio) {
                console.log("Stopping audio on unmount")
                currentAudio.pause()
                currentAudio.currentTime = 0
            }
        }
    }, [currentAudio])

    const fillerPhrases = [
        "Let me check that for you...",
        "One moment please...",
        "I'm looking into that...",
        "Give me just a second...",
        "Let me find that information..."
    ]

    const playFillerPhrase = async () => {
        // Don't play filler if already playing, cancelled, or if processing is done
        if (isFillerPlayingRef.current || fillerCancelledRef.current) {
            console.log('🎭 Filler skipped - already playing or cancelled')
            return
        }

        const randomFiller = fillerPhrases[Math.floor(Math.random() * fillerPhrases.length)]
        console.log('🎭 Preparing filler:', randomFiller)
        isFillerPlayingRef.current = true

        try {
            const response = await axios.post(`${API_BASE_URL}/tts`, {
                text: randomFiller,
                sector: sector.id
            })

            // 🔴 CRITICAL: Check if filler was cancelled during TTS request
            if (fillerCancelledRef.current) {
                console.log('🎭 Filler cancelled after TTS - not playing')
                isFillerPlayingRef.current = false
                return
            }

            if (response.data.audio) {
                // Stop any current audio before playing filler
                if (currentAudio) {
                    currentAudio.pause()
                }

                const audio = new Audio(`data:audio/mp3;base64,${response.data.audio}`)
                setCurrentAudio(audio) // Track filler audio so it can be stopped
                audio.play().catch(err => {
                    console.log("Filler blocked by browser")
                    isFillerPlayingRef.current = false
                })

                audio.onended = () => {
                    isFillerPlayingRef.current = false
                    if (currentAudio === audio) {
                        setCurrentAudio(null)
                    }
                }
            } else {
                isFillerPlayingRef.current = false
            }
        } catch (error) {
            console.log("Filler TTS failed")
            isFillerPlayingRef.current = false
        }
    }

    // 🎯 INTERRUPTION HANDLER: Stop AI audio and filler when user interrupts
    const handleInterruption = () => {
        console.log('🔄 Handling interruption...')

        // Stop any playing audio immediately
        if (currentAudio) {
            currentAudio.pause()
            currentAudio.currentTime = 0
            setCurrentAudio(null)
        }

        // Clear filler timer and flag
        if (fillerTimerRef.current) {
            clearTimeout(fillerTimerRef.current)
            fillerTimerRef.current = null
        }
        isFillerPlayingRef.current = false

        // Mark AI as not speaking
        setIsAISpeaking(false)
    }

    const startRecording = () => {
        if (recognitionRef.current) {
            setTranscriptionPreview('')
            transcriptionRef.current = ''
            try {
                recognitionRef.current.start()
                setIsRecording(true)
                console.log('🎤 Recording started - User can interrupt anytime')
            } catch (e) {
                // If already started, ignore the error
                if (e.message && e.message.includes('already started')) {
                    console.log('🎤 Recognition already active')
                } else {
                    console.error("Error starting recognition:", e)
                }
            }
        }
    }

    const stopRecording = () => {
        if (recognitionRef.current) {
            recognitionRef.current.stop()
            setIsRecording(false)

            // Use ref to get the latest transcript
            const textToSubmit = transcriptionRef.current

            if (textToSubmit && textToSubmit.trim()) {
                console.log("Stopping and submitting:", textToSubmit)
                // Submit query - filler logic is now inside handleVoiceTextSubmit
                handleVoiceTextSubmit(textToSubmit)
            } else {
                // If nothing was said, restart recording (keep listening)
                // But give a small delay to avoid rapid loops
                setTimeout(() => {
                    if (!isProcessing) startRecording()
                }, 500)
            }
        }
    }

    const handleVoiceTextSubmit = async (text) => {
        const startTime = performance.now()
        console.log(`⏱️ Request started at: ${new Date().toLocaleTimeString()}`)

        setIsProcessing(true)

        // 🔴 Reset filler cancellation flag at start of new request
        fillerCancelledRef.current = false

        // 🔇 Skip fillers for simple greetings/thanks - they respond fast and filler overlaps
        const simpleQueryPatterns = [
            /^(hi|hello|hey|good\s*(morning|afternoon|evening|night)|namaste)/i,
            /^(thank\s*you|thanks|thankyou|dhanyavaad|shukriya)/i,
            /^(bye|goodbye|see\s*you|take\s*care|good\s*bye)/i,
            /^(ok|okay|alright|fine|got\s*it|understood)/i,
            /^(yes|no|yeah|nope|yep|nah)/i,
            /^(hmm|hm|ah|oh|uh)/i
        ]

        const isSimpleQuery = simpleQueryPatterns.some(pattern => pattern.test(text.trim()))

        if (isSimpleQuery) {
            console.log('⚡ Simple query detected - skipping filler')
        }

        // Smart Filler Logic: Play filler ONLY for complex queries that take time
        // Skip fillers for greetings, thanks, and other fast responses
        // Increased delay to 2500ms to avoid clash with most responses
        if (!isSimpleQuery) {
            fillerTimerRef.current = setTimeout(() => {
                console.log("⏳ Response taking time, playing filler...")
                playFillerPhrase()
            }, 2500)
        }

        try {
            const timestamp = new Date().toISOString()
            setMessages(prev => [...prev, {
                type: 'user',
                text: text,
                timestamp
            }])

            const chatStart = performance.now()
            const chatResponse = await axios.post(`${API_BASE_URL}/chat`, {
                query: text,
                sector: sector.id,
                conversation_history: messages, // Send conversation context
                language: selectedLanguage // Send selected language
            })

            const chatEnd = performance.now()
            console.log(`🤖 LLM Response time: ${(chatEnd - chatStart).toFixed(0)}ms`)

            const { response: aiResponse, needs_human_handoff, handoff_reason } = chatResponse.data

            // Check for human handoff
            if (needs_human_handoff) {
                console.log('🚨 Human handoff required:', handoff_reason)
                setNeedsHumanHandoff(true)
                // Show handoff UI
                setTimeout(() => {
                    alert(`Human Agent Required\n\nReason: ${handoff_reason}\n\nA human agent will be connected shortly. Please hold on.`)
                }, 500)
            }

            const ttsStart = performance.now()
            const ttsResponse = await axios.post(`${API_BASE_URL}/tts`, {
                text: aiResponse,
                sector: sector.id
            })
            const ttsEnd = performance.now()
            console.log(`🔊 TTS time: ${(ttsEnd - ttsStart).toFixed(0)}ms`)

            // 🔴 IMMEDIATELY cancel filler - set flag first to prevent any pending filler from playing
            fillerCancelledRef.current = true

            // Cancel filler timer
            if (fillerTimerRef.current) {
                clearTimeout(fillerTimerRef.current)
                fillerTimerRef.current = null
            }

            // Stop any playing filler audio and wait a moment
            if (currentAudio) {
                console.log('🔇 Stopping filler audio for actual response')
                currentAudio.pause()
                currentAudio.currentTime = 0
                setCurrentAudio(null)
            }
            isFillerPlayingRef.current = false

            // Small delay to ensure filler audio is fully stopped
            await new Promise(resolve => setTimeout(resolve, 150))

            const totalTime = performance.now() - startTime
            console.log(`✅ Total latency: ${totalTime.toFixed(0)}ms (${(totalTime / 1000).toFixed(2)}s)`)

            const audioBase64 = ttsResponse.data.audio

            setMessages(prev => [...prev, {
                type: 'ai',
                text: aiResponse,
                audio: audioBase64,
                timestamp: timestamp
            }])

            if (audioBase64) {
                // 🎯 Start recording BEFORE playing audio to enable interruption
                setIsAISpeaking(true)

                // Start listening immediately so user can interrupt
                setTimeout(() => {
                    if (!isRecording) {
                        startRecording()
                    }
                }, 100)

                // Play AI response
                playAudioResponse(audioBase64, () => {
                    console.log("AI response ended naturally")
                    setIsAISpeaking(false)

                    // Auto-restart mic after AI finishes speaking
                    if (callMode) {
                        console.log('🎤 Restarting mic for next question...')
                        setTimeout(() => {
                            startRecording()
                        }, 300) // Small delay for natural conversation flow
                    }
                })
            } else {
                setIsAISpeaking(false)
                // Auto-restart mic
                if (callMode) {
                    startRecording()
                }
            }

        } catch (error) {
            // Ensure timer is cleared on error
            if (fillerTimerRef.current) {
                clearTimeout(fillerTimerRef.current)
                fillerTimerRef.current = null
            }
            console.error('Error processing voice input:', error)
            alert('Error processing voice input. Please try again.')
            // 📞 Keep listening even after error in phone call mode
            if (callMode) {
                startRecording()
            }
        } finally {
            setIsProcessing(false)
        }
    }

    const handleTextSubmit = async (e) => {
        e.preventDefault()
        if (!textInput.trim()) return

        const userMessage = textInput
        setTextInput('')
        handleVoiceTextSubmit(userMessage)
    }

    const playAudioResponse = (audioBase64, onEnded) => {
        try {
            if (currentAudio) {
                currentAudio.pause()
                currentAudio.currentTime = 0
            }

            const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`)
            setCurrentAudio(audio)

            audio.onended = () => {
                setCurrentAudio(null)
                if (onEnded) onEnded()
            }

            audio.play()
        } catch (error) {
            console.error('Error playing audio:', error)
            if (onEnded) onEnded()
        }
    }

    const clearConversation = () => {
        setMessages([])
        setTranscriptionPreview('')
        if (currentAudio) {
            currentAudio.pause()
            setCurrentAudio(null)
        }
    }

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    return (
        <div className="voice-agent-page embedded">
            {/* Page Header */}
            <div className="agent-header">
                <div className="agent-info">
                    <span className="agent-sector-icon">{sector.icon}</span>
                    <div>
                        <h2 className="agent-title">{sector.title}</h2>
                        <p className="agent-subtitle">{sector.subtitle}</p>
                    </div>
                </div>
                <div className="agent-badges">
                    <span className="badge">🌐 {selectedLanguage === 'en' ? 'English' : selectedLanguage === 'hi' ? 'Hindi' : selectedLanguage === 'ta' ? 'Tamil' : 'Multi-lang'}</span>
                    <span className="badge success">⚡ Sub-2s Latency</span>
                </div>
            </div>

            <div className="agent-content-clean">
                {/* LEFT SIDE - Conversation Area */}
                <motion.div
                    className="conversation-panel"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4 }}
                >
                    <div className="panel-header">
                        <h3>💬 Conversation</h3>
                        {messages.length > 0 && (
                            <button className="clear-btn-small" onClick={clearConversation}>
                                <Trash2 size={16} />
                            </button>
                        )}
                    </div>

                    <div className="messages-area" ref={messagesContainerRef}>
                        {messages.length === 0 ? (
                            <div className="empty-chat">
                                <div className="empty-icon">💬</div>
                                <p>Start a conversation by clicking the mic or typing below</p>
                            </div>
                        ) : (
                            messages.map((message, index) => (
                                <motion.div
                                    key={index}
                                    className={`chat-bubble ${message.type}`}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <div className="bubble-header">
                                        <span className="speaker">{message.type === 'user' ? '👤 You' : '🤖 AI Agent'}</span>
                                        <span className="time">{formatTime(message.timestamp)}</span>
                                    </div>
                                    <p className="bubble-text">{message.text}</p>
                                    {message.audio && (
                                        <button className="replay-btn" onClick={() => playAudioResponse(message.audio)}>
                                            <Volume2 size={14} /> Replay
                                        </button>
                                    )}
                                </motion.div>
                            ))
                        )}
                    </div>

                    {/* Text Input */}
                    <form className="chat-input-form" onSubmit={handleTextSubmit}>
                        <input
                            type="text"
                            value={textInput}
                            onChange={(e) => setTextInput(e.target.value)}
                            placeholder="Type a message..."
                            disabled={isProcessing}
                            className="chat-input"
                        />
                        <button type="submit" className="send-btn-clean" disabled={!textInput.trim() || isProcessing}>
                            <Send size={18} />
                        </button>
                    </form>
                </motion.div>

                {/* RIGHT SIDE - Voice Control & Samples */}
                <motion.div
                    className="control-panel"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: 0.1 }}
                >
                    {/* Mic Section */}
                    <div className="mic-section">
                        {/* Language Selector */}
                        <div className="language-row">
                            <select
                                value={selectedLanguage}
                                onChange={(e) => setSelectedLanguage(e.target.value)}
                                className="lang-select"
                            >
                                <option value="en">🌐 English</option>
                                <option value="hi">🇮🇳 Hindi</option>
                            </select>
                        </div>

                        {/* Human Handoff Alert */}
                        {needsHumanHandoff && (
                            <div className="handoff-banner">
                                🚨 Connecting to human agent...
                            </div>
                        )}

                        {/* Mic Button */}
                        <div className="mic-area">
                            <motion.button
                                className={`mic-btn ${isRecording ? 'recording' : ''} ${isAISpeaking ? 'ai-speaking' : ''}`}
                                onClick={isRecording ? stopRecording : startRecording}
                                disabled={isProcessing}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <Mic size={36} />
                            </motion.button>
                            <p className="mic-label">
                                {isAISpeaking ? '🔊 Speaking...' :
                                    isRecording ? '🔴 Listening' :
                                        isProcessing ? '⏳ Processing' : '🎤 Tap to speak'}
                            </p>
                        </div>

                        {/* Live Transcription */}
                        {(isRecording || transcriptionPreview) && (
                            <div className="live-text">
                                <span className="live-dot"></span>
                                {transcriptionPreview || 'Listening...'}
                            </div>
                        )}

                        {/* Quick Tips */}
                        {isAISpeaking && (
                            <div className="tip-banner">
                                💡 Interrupt anytime by speaking
                            </div>
                        )}
                    </div>

                    {/* Sample Queries with Language Tabs */}
                    <div className="samples-section">
                        <h4>💡 Try asking</h4>

                        {/* Language Tabs */}
                        <div className="sample-lang-tabs">
                            <button
                                className={`sample-lang-tab ${sampleLangTab === 'english' ? 'active' : ''}`}
                                onClick={() => setSampleLangTab('english')}
                            >
                                🌐 English
                            </button>
                            <button
                                className={`sample-lang-tab ${sampleLangTab === 'hinglish' ? 'active' : ''}`}
                                onClick={() => setSampleLangTab('hinglish')}
                            >
                                🇮🇳 Hinglish
                            </button>
                        </div>

                        {/* Scrollable Sample List */}
                        <div className="sample-list-scroll">
                            {(() => {
                                const queries = sector.sampleQueries || []
                                // Split queries into 2 groups: English (first half), Hinglish (second half)
                                const totalQueries = queries.length
                                const groupSize = Math.ceil(totalQueries / 2)

                                let filteredQueries = []
                                if (sampleLangTab === 'english') {
                                    filteredQueries = queries.slice(0, groupSize)
                                } else {
                                    filteredQueries = queries.slice(groupSize)
                                }

                                return filteredQueries.map((query, index) => (
                                    <button
                                        key={index}
                                        className="sample-btn"
                                        onClick={() => setTextInput(query)}
                                    >
                                        {query}
                                    </button>
                                ))
                            })()}
                        </div>
                    </div>

                    {/* Quick Features */}
                    <div className="features-strip">
                        <span className="feature-tag">🛑 Interruption</span>
                        <span className="feature-tag">🔄 Context Memory</span>
                        <span className="feature-tag">🤝 Human Handoff</span>
                    </div>
                </motion.div>
            </div>
        </div>
    )
}

export default VoiceAgentPage
