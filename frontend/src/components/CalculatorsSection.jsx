import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Calculator, TrendingDown, Brain, Ticket, FileSpreadsheet, X, Download, ChevronRight, Clock, Users, Target, DollarSign, AlertTriangle, Workflow, TrendingUp } from 'lucide-react'
import XLSX from 'xlsx-js-style'
import './CalculatorsSection.css'

// Format Indian currency
const formatINR = (amount) => {
    if (amount >= 10000000) {
        return `₹${(amount / 10000000).toFixed(2)} Cr`
    } else if (amount >= 100000) {
        return `₹${(amount / 100000).toFixed(2)} L`
    }
    return `₹${amount.toLocaleString('en-IN')}`
}

// All 10 Calculator definitions
const CALCULATORS = [
    {
        id: 'attrition',
        title: 'Attrition Cost Analyzer',
        subtitle: 'Uncover the hidden cost of employee turnover',
        icon: TrendingDown,
        color: '#ef4444',
        impact: '₹25-50L for 50 agents'
    },
    {
        id: 'ai-readiness',
        title: 'AI Readiness Diagnostic',
        subtitle: 'Measure your automation readiness score',
        icon: Brain,
        color: '#8b5cf6',
        impact: 'Score 0-100'
    },
    {
        id: 'ticket-deflection',
        title: 'Ticket Deflection ROI',
        subtitle: 'Calculate savings from automation',
        icon: Ticket,
        color: '#10b981',
        impact: '50-200% ROI'
    },
    {
        id: 'manual-work',
        title: 'Hidden Costs of Manual Work',
        subtitle: 'Quantify time waste from manual tasks',
        icon: Clock,
        color: '#f59e0b',
        impact: '₹15-50L+ per year'
    },
    {
        id: 'automation-potential',
        title: 'Automation Potential Scorecard',
        subtitle: 'Identify which processes to automate first',
        icon: Target,
        color: '#06b6d4',
        impact: '40-80% automatable'
    },
    {
        id: 'ltv-rescue',
        title: 'Customer LTV Rescue Tool',
        subtitle: 'Calculate revenue at risk from poor service',
        icon: DollarSign,
        color: '#ec4899',
        impact: '₹50-500Cr at risk'
    },
    {
        id: 'scalability',
        title: 'Scalability Stress Test',
        subtitle: 'Forecast when operations will break',
        icon: TrendingUp,
        color: '#14b8a6',
        impact: 'Breaking point month'
    },
    {
        id: 'bottleneck',
        title: 'Process Bottleneck Identifier',
        subtitle: 'Find your most costly process bottlenecks',
        icon: Workflow,
        color: '#f97316',
        impact: '₹10-100L per bottleneck'
    },
    {
        id: 'aht-reduction',
        title: 'AHT Reduction Planner',
        subtitle: 'Calculate capacity gains from faster calls',
        icon: Clock,
        color: '#84cc16',
        impact: '40-50% throughput increase'
    },
    {
        id: 'sla-failure',
        title: 'SLA Failure Cost Calculator',
        subtitle: 'Quantify the cost of missed SLAs',
        icon: AlertTriangle,
        color: '#dc2626',
        impact: '₹10-100Cr for large ops'
    }
]

// Attrition Calculator Component
function AttritionCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({
        teamSize: 50,
        avgSalary: 250000,
        attritionRate: 35,
        costPerSeparation: 90000,
        hiringCost: 50000,
        trainingCost: 80000,
        rampUpLoss: 90000
    })

    const [results, setResults] = useState(null)

    const calculate = () => {
        const agentsLeaving = inputs.teamSize * (inputs.attritionRate / 100)
        const separationCost = agentsLeaving * inputs.costPerSeparation
        const recruitmentCost = agentsLeaving * inputs.hiringCost
        const trainingCostTotal = agentsLeaving * inputs.trainingCost
        const rampUpCost = agentsLeaving * inputs.rampUpLoss
        const baseTeamSalary = inputs.teamSize * inputs.avgSalary
        const moraleImpact = baseTeamSalary * (inputs.attritionRate / 100) * 0.15

        const totalAttritionCost = separationCost + recruitmentCost + trainingCostTotal + rampUpCost + moraleImpact
        const costPerAgent = totalAttritionCost / inputs.teamSize
        const costVsSalary = (totalAttritionCost / baseTeamSalary) * 100

        setResults({
            agentsLeaving: Math.round(agentsLeaving * 10) / 10,
            separationCost,
            recruitmentCost,
            trainingCostTotal,
            rampUpCost,
            moraleImpact,
            totalAttritionCost,
            costPerAgent,
            costVsSalary,
            baseTeamSalary
        })
    }

    const exportToExcel = () => {
        if (!results) return

        const data = {
            'Attrition Cost Analysis': {
                'Input Parameters': {
                    'Team Size': inputs.teamSize,
                    'Average Salary (₹)': inputs.avgSalary,
                    'Attrition Rate (%)': inputs.attritionRate,
                    'Cost Per Separation (₹)': inputs.costPerSeparation,
                    'Hiring Cost Per Agent (₹)': inputs.hiringCost,
                    'Training Cost Per Agent (₹)': inputs.trainingCost,
                    'Ramp-up Loss Per Agent (₹)': inputs.rampUpLoss
                },
                'Results': {
                    'Agents Leaving Per Year': results.agentsLeaving,
                    'Separation Cost (₹)': results.separationCost,
                    'Recruitment Cost (₹)': results.recruitmentCost,
                    'Training Cost (₹)': results.trainingCostTotal,
                    'Ramp-up Productivity Loss (₹)': results.rampUpCost,
                    'Team Morale Impact (₹)': results.moraleImpact,
                    'TOTAL ATTRITION COST (₹)': results.totalAttritionCost,
                    'Cost Per Agent (₹)': results.costPerAgent,
                    'Attrition Cost vs Salary (%)': results.costVsSalary.toFixed(1)
                }
            }
        }
        onExport(data, 'Attrition_Cost_Analysis')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info">
                    <TrendingDown size={28} color="#ef4444" />
                    <h2>Attrition Cost Analyzer</h2>
                </div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>

            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Your Data</h3>
                    <div className="input-grid">
                        <div className="input-group">
                            <label>Team Size (Agents)</label>
                            <input
                                type="number"
                                value={inputs.teamSize}
                                onChange={(e) => setInputs({ ...inputs, teamSize: Number(e.target.value) })}
                            />
                        </div>
                        <div className="input-group">
                            <label>Avg Annual Salary (₹)</label>
                            <input
                                type="number"
                                value={inputs.avgSalary}
                                onChange={(e) => setInputs({ ...inputs, avgSalary: Number(e.target.value) })}
                            />
                        </div>
                        <div className="input-group">
                            <label>Annual Attrition Rate (%)</label>
                            <input
                                type="number"
                                value={inputs.attritionRate}
                                onChange={(e) => setInputs({ ...inputs, attritionRate: Number(e.target.value) })}
                            />
                        </div>
                        <div className="input-group">
                            <label>Cost Per Separation (₹)</label>
                            <input
                                type="number"
                                value={inputs.costPerSeparation}
                                onChange={(e) => setInputs({ ...inputs, costPerSeparation: Number(e.target.value) })}
                            />
                        </div>
                        <div className="input-group">
                            <label>Hiring Cost Per Agent (₹)</label>
                            <input
                                type="number"
                                value={inputs.hiringCost}
                                onChange={(e) => setInputs({ ...inputs, hiringCost: Number(e.target.value) })}
                            />
                        </div>
                        <div className="input-group">
                            <label>Training Cost Per Agent (₹)</label>
                            <input
                                type="number"
                                value={inputs.trainingCost}
                                onChange={(e) => setInputs({ ...inputs, trainingCost: Number(e.target.value) })}
                            />
                        </div>
                        <div className="input-group">
                            <label>Ramp-up Loss Per Agent (₹)</label>
                            <input
                                type="number"
                                value={inputs.rampUpLoss}
                                onChange={(e) => setInputs({ ...inputs, rampUpLoss: Number(e.target.value) })}
                            />
                        </div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}>
                        <Calculator size={20} /> Calculate Impact
                    </button>
                </div>

                {results && (
                    <div className="calc-results">
                        <h3>📈 Your Results</h3>

                        <div className="result-highlight danger">
                            <span className="result-label">Total Annual Attrition Cost</span>
                            <span className="result-value">{formatINR(results.totalAttritionCost)}</span>
                        </div>

                        <div className="result-breakdown">
                            <div className="result-item">
                                <span>Agents Leaving/Year</span>
                                <span>{results.agentsLeaving}</span>
                            </div>
                            <div className="result-item">
                                <span>Separation Costs</span>
                                <span>{formatINR(results.separationCost)}</span>
                            </div>
                            <div className="result-item">
                                <span>Recruitment Costs</span>
                                <span>{formatINR(results.recruitmentCost)}</span>
                            </div>
                            <div className="result-item">
                                <span>Training Costs</span>
                                <span>{formatINR(results.trainingCostTotal)}</span>
                            </div>
                            <div className="result-item">
                                <span>Ramp-up Productivity Loss</span>
                                <span>{formatINR(results.rampUpCost)}</span>
                            </div>
                            <div className="result-item">
                                <span>Team Morale Impact</span>
                                <span>{formatINR(results.moraleImpact)}</span>
                            </div>
                        </div>

                        <div className="result-insights">
                            <div className="insight-card">
                                <span className="insight-label">Cost Per Agent</span>
                                <span className="insight-value">{formatINR(results.costPerAgent)}</span>
                            </div>
                            <div className="insight-card warning">
                                <span className="insight-label">Attrition Cost vs Salary</span>
                                <span className="insight-value">{results.costVsSalary.toFixed(0)}%</span>
                            </div>
                        </div>

                        <div className="result-message">
                            ⚠️ Your attrition costs almost equal your entire salary budget!
                        </div>

                        <button className="export-btn" onClick={exportToExcel}>
                            <Download size={20} /> Export to Excel
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

// AI Readiness Calculator Component
function AIReadinessCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({
        docQuality: 65,
        standardization: 70,
        repetitiveness: 75,
        dataCompleteness: 75,
        dataAccuracy: 80,
        dataAccessibility: 60,
        systemIntegration: 65,
        apiAvailability: 40,
        uptime: 85,
        techProficiency: 55,
        aiLiteracy: 45
    })

    const [results, setResults] = useState(null)

    const calculate = () => {
        const processScore = (inputs.docQuality * 0.40) + (inputs.standardization * 0.30) + (inputs.repetitiveness * 0.30)
        const dataScore = (inputs.dataCompleteness * 0.40) + (inputs.dataAccuracy * 0.35) + (inputs.dataAccessibility * 0.25)
        const infraScore = (inputs.systemIntegration * 0.40) + (inputs.apiAvailability * 0.30) + (inputs.uptime * 0.30)
        const teamScore = (inputs.techProficiency * 0.50) + (inputs.aiLiteracy * 0.50)

        const overallScore = (processScore * 0.25) + (dataScore * 0.25) + (infraScore * 0.25) + (teamScore * 0.25)

        let readinessLevel, timeline, expectedROI
        if (overallScore >= 80) {
            readinessLevel = 'High Readiness'
            timeline = '3-6 months'
            expectedROI = '200-400%'
        } else if (overallScore >= 60) {
            readinessLevel = 'Moderate Readiness'
            timeline = '6-12 months'
            expectedROI = '100-200%'
        } else if (overallScore >= 40) {
            readinessLevel = 'Low Readiness'
            timeline = '12-18 months'
            expectedROI = '50-100%'
        } else {
            readinessLevel = 'Not Ready'
            timeline = '18+ months'
            expectedROI = 'TBD after prep'
        }

        setResults({
            processScore: Math.round(processScore * 10) / 10,
            dataScore: Math.round(dataScore * 10) / 10,
            infraScore: Math.round(infraScore * 10) / 10,
            teamScore: Math.round(teamScore * 10) / 10,
            overallScore: Math.round(overallScore * 10) / 10,
            readinessLevel,
            timeline,
            expectedROI
        })
    }

    const exportToExcel = () => {
        if (!results) return

        const data = {
            'AI Readiness Diagnostic': {
                'Process Scores': {
                    'Documentation Quality': inputs.docQuality,
                    'Standardization': inputs.standardization,
                    'Repetitiveness': inputs.repetitiveness,
                    'Process Score': results.processScore
                },
                'Data Scores': {
                    'Completeness': inputs.dataCompleteness,
                    'Accuracy': inputs.dataAccuracy,
                    'Accessibility': inputs.dataAccessibility,
                    'Data Score': results.dataScore
                },
                'Infrastructure Scores': {
                    'System Integration': inputs.systemIntegration,
                    'API Availability': inputs.apiAvailability,
                    'Uptime': inputs.uptime,
                    'Infra Score': results.infraScore
                },
                'Team Scores': {
                    'Technical Proficiency': inputs.techProficiency,
                    'AI Literacy': inputs.aiLiteracy,
                    'Team Score': results.teamScore
                },
                'Overall Results': {
                    'OVERALL AI READINESS SCORE': results.overallScore,
                    'Readiness Level': results.readinessLevel,
                    'Implementation Timeline': results.timeline,
                    'Expected ROI (24 months)': results.expectedROI
                }
            }
        }
        onExport(data, 'AI_Readiness_Diagnostic')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info">
                    <Brain size={28} color="#8b5cf6" />
                    <h2>AI Readiness Diagnostic</h2>
                </div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>

            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📋 Rate Your Organization (0-100)</h3>

                    <div className="input-section">
                        <h4>Process Maturity</h4>
                        <div className="input-grid">
                            <div className="input-group">
                                <label>Documentation Quality (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.docQuality}
                                    onChange={(e) => setInputs({ ...inputs, docQuality: Number(e.target.value) })} />
                            </div>
                            <div className="input-group">
                                <label>Standardization (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.standardization}
                                    onChange={(e) => setInputs({ ...inputs, standardization: Number(e.target.value) })} />
                            </div>
                            <div className="input-group">
                                <label>Repetitiveness (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.repetitiveness}
                                    onChange={(e) => setInputs({ ...inputs, repetitiveness: Number(e.target.value) })} />
                            </div>
                        </div>
                    </div>

                    <div className="input-section">
                        <h4>Data Quality</h4>
                        <div className="input-grid">
                            <div className="input-group">
                                <label>Completeness (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.dataCompleteness}
                                    onChange={(e) => setInputs({ ...inputs, dataCompleteness: Number(e.target.value) })} />
                            </div>
                            <div className="input-group">
                                <label>Accuracy (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.dataAccuracy}
                                    onChange={(e) => setInputs({ ...inputs, dataAccuracy: Number(e.target.value) })} />
                            </div>
                            <div className="input-group">
                                <label>Accessibility (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.dataAccessibility}
                                    onChange={(e) => setInputs({ ...inputs, dataAccessibility: Number(e.target.value) })} />
                            </div>
                        </div>
                    </div>

                    <div className="input-section">
                        <h4>Technical Infrastructure</h4>
                        <div className="input-grid">
                            <div className="input-group">
                                <label>System Integration (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.systemIntegration}
                                    onChange={(e) => setInputs({ ...inputs, systemIntegration: Number(e.target.value) })} />
                            </div>
                            <div className="input-group">
                                <label>API Availability (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.apiAvailability}
                                    onChange={(e) => setInputs({ ...inputs, apiAvailability: Number(e.target.value) })} />
                            </div>
                            <div className="input-group">
                                <label>Uptime/Reliability (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.uptime}
                                    onChange={(e) => setInputs({ ...inputs, uptime: Number(e.target.value) })} />
                            </div>
                        </div>
                    </div>

                    <div className="input-section">
                        <h4>Team Skills</h4>
                        <div className="input-grid">
                            <div className="input-group">
                                <label>Technical Proficiency (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.techProficiency}
                                    onChange={(e) => setInputs({ ...inputs, techProficiency: Number(e.target.value) })} />
                            </div>
                            <div className="input-group">
                                <label>AI Literacy (0-100)</label>
                                <input type="number" min="0" max="100" value={inputs.aiLiteracy}
                                    onChange={(e) => setInputs({ ...inputs, aiLiteracy: Number(e.target.value) })} />
                            </div>
                        </div>
                    </div>

                    <button className="calculate-btn" onClick={calculate}>
                        <Calculator size={20} /> Calculate Readiness Score
                    </button>
                </div>

                {results && (
                    <div className="calc-results">
                        <h3>🎯 Your AI Readiness Score</h3>

                        <div className={`result-highlight ${results.overallScore >= 60 ? 'success' : 'warning'}`}>
                            <span className="result-label">Overall Score</span>
                            <span className="result-value score">{results.overallScore}/100</span>
                        </div>

                        <div className="score-bars">
                            <div className="score-bar">
                                <span>Process Maturity</span>
                                <div className="bar-container">
                                    <div className="bar-fill" style={{ width: `${results.processScore}%` }}></div>
                                </div>
                                <span>{results.processScore}</span>
                            </div>
                            <div className="score-bar">
                                <span>Data Quality</span>
                                <div className="bar-container">
                                    <div className="bar-fill" style={{ width: `${results.dataScore}%` }}></div>
                                </div>
                                <span>{results.dataScore}</span>
                            </div>
                            <div className="score-bar">
                                <span>Infrastructure</span>
                                <div className="bar-container">
                                    <div className="bar-fill" style={{ width: `${results.infraScore}%` }}></div>
                                </div>
                                <span>{results.infraScore}</span>
                            </div>
                            <div className="score-bar">
                                <span>Team Skills</span>
                                <div className="bar-container">
                                    <div className="bar-fill" style={{ width: `${results.teamScore}%` }}></div>
                                </div>
                                <span>{results.teamScore}</span>
                            </div>
                        </div>

                        <div className="result-insights">
                            <div className="insight-card">
                                <span className="insight-label">Readiness Level</span>
                                <span className="insight-value">{results.readinessLevel}</span>
                            </div>
                            <div className="insight-card">
                                <span className="insight-label">Implementation Timeline</span>
                                <span className="insight-value">{results.timeline}</span>
                            </div>
                            <div className="insight-card success">
                                <span className="insight-label">Expected ROI (24 mo)</span>
                                <span className="insight-value">{results.expectedROI}</span>
                            </div>
                        </div>

                        <button className="export-btn" onClick={exportToExcel}>
                            <Download size={20} /> Export to Excel
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Ticket Deflection ROI Calculator
function TicketDeflectionCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({
        annualTickets: 500000,
        teamSize: 50,
        avgSalary: 250000,
        overhead: 4000000,
        deflectionRate: 30,
        implementationCost: 5000000,
        monthlyPlatformCost: 200000
    })

    const [results, setResults] = useState(null)

    const calculate = () => {
        const totalSupportCost = (inputs.teamSize * inputs.avgSalary) + inputs.overhead
        const costPerTicket = totalSupportCost / inputs.annualTickets
        const deflectedTickets = inputs.annualTickets * (inputs.deflectionRate / 100)
        const annualSavings = deflectedTickets * costPerTicket
        const monthlySavings = annualSavings / 12
        const paybackPeriod = inputs.implementationCost / monthlySavings
        const annualPlatformCost = inputs.monthlyPlatformCost * 12

        // 24-month calculation with ramp-up
        const savingsFirst6Months = (monthlySavings * 0.5) * 6
        const savingsNext18Months = monthlySavings * 18
        const totalSavings24Months = savingsFirst6Months + savingsNext18Months
        const totalCosts24Months = inputs.implementationCost + (annualPlatformCost * 2)
        const netSavings24Months = totalSavings24Months - totalCosts24Months
        const roi24Months = (netSavings24Months / inputs.implementationCost) * 100

        setResults({
            costPerTicket: Math.round(costPerTicket),
            deflectedTickets,
            annualSavings,
            monthlySavings,
            paybackPeriod: Math.round(paybackPeriod * 10) / 10,
            totalSavings24Months,
            netSavings24Months,
            roi24Months: Math.round(roi24Months)
        })
    }

    const exportToExcel = () => {
        if (!results) return

        const data = {
            'Ticket Deflection ROI': {
                'Input Parameters': {
                    'Annual Tickets': inputs.annualTickets,
                    'Team Size': inputs.teamSize,
                    'Average Salary (₹)': inputs.avgSalary,
                    'Overhead (₹)': inputs.overhead,
                    'Deflection Rate (%)': inputs.deflectionRate,
                    'Implementation Cost (₹)': inputs.implementationCost,
                    'Monthly Platform Cost (₹)': inputs.monthlyPlatformCost
                },
                'Results': {
                    'Cost Per Ticket (₹)': results.costPerTicket,
                    'Deflected Tickets/Year': results.deflectedTickets,
                    'Annual Savings (₹)': results.annualSavings,
                    'Monthly Savings (₹)': results.monthlySavings,
                    'Payback Period (Months)': results.paybackPeriod,
                    'Total Savings (24 months)': results.totalSavings24Months,
                    'Net Savings (24 months)': results.netSavings24Months,
                    'ROI (24 months) %': results.roi24Months
                }
            }
        }
        onExport(data, 'Ticket_Deflection_ROI')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info">
                    <Ticket size={28} color="#10b981" />
                    <h2>Ticket Deflection ROI Modeler</h2>
                </div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>

            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Your Data</h3>
                    <div className="input-grid">
                        <div className="input-group">
                            <label>Annual Tickets</label>
                            <input type="number" value={inputs.annualTickets}
                                onChange={(e) => setInputs({ ...inputs, annualTickets: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Team Size (Agents)</label>
                            <input type="number" value={inputs.teamSize}
                                onChange={(e) => setInputs({ ...inputs, teamSize: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Avg Annual Salary (₹)</label>
                            <input type="number" value={inputs.avgSalary}
                                onChange={(e) => setInputs({ ...inputs, avgSalary: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Annual Overhead (₹)</label>
                            <input type="number" value={inputs.overhead}
                                onChange={(e) => setInputs({ ...inputs, overhead: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Deflection Rate (%)</label>
                            <input type="number" value={inputs.deflectionRate}
                                onChange={(e) => setInputs({ ...inputs, deflectionRate: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Implementation Cost (₹)</label>
                            <input type="number" value={inputs.implementationCost}
                                onChange={(e) => setInputs({ ...inputs, implementationCost: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Monthly Platform Cost (₹)</label>
                            <input type="number" value={inputs.monthlyPlatformCost}
                                onChange={(e) => setInputs({ ...inputs, monthlyPlatformCost: Number(e.target.value) })} />
                        </div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}>
                        <Calculator size={20} /> Calculate ROI
                    </button>
                </div>

                {results && (
                    <div className="calc-results">
                        <h3>💰 Your ROI Results</h3>

                        <div className="result-highlight success">
                            <span className="result-label">24-Month ROI</span>
                            <span className="result-value">{results.roi24Months}%</span>
                        </div>

                        <div className="result-breakdown">
                            <div className="result-item">
                                <span>Cost Per Ticket</span>
                                <span>₹{results.costPerTicket}</span>
                            </div>
                            <div className="result-item">
                                <span>Tickets Deflected/Year</span>
                                <span>{results.deflectedTickets.toLocaleString()}</span>
                            </div>
                            <div className="result-item">
                                <span>Annual Savings</span>
                                <span>{formatINR(results.annualSavings)}</span>
                            </div>
                            <div className="result-item">
                                <span>Monthly Savings</span>
                                <span>{formatINR(results.monthlySavings)}</span>
                            </div>
                        </div>

                        <div className="result-insights">
                            <div className="insight-card success">
                                <span className="insight-label">Payback Period</span>
                                <span className="insight-value">{results.paybackPeriod} months</span>
                            </div>
                            <div className="insight-card">
                                <span className="insight-label">Net Savings (24 mo)</span>
                                <span className="insight-value">{formatINR(results.netSavings24Months)}</span>
                            </div>
                        </div>

                        <div className="result-message success">
                            💡 For every ₹1 invested, you get ₹{(results.roi24Months / 100).toFixed(2)} back!
                        </div>

                        <button className="export-btn" onClick={exportToExcel}>
                            <Download size={20} /> Export to Excel
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Calculator 4: Hidden Costs of Manual Work
function ManualWorkCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({
        teamSize: 50,
        dailyCalls: 20,
        minutesPerSummary: 5,
        workingDays: 245,
        hourlyRate: 200
    })
    const [results, setResults] = useState(null)

    const calculate = () => {
        const totalMinutes = inputs.dailyCalls * inputs.minutesPerSummary * inputs.workingDays
        const hoursPerAgent = totalMinutes / 60
        const costPerAgent = hoursPerAgent * inputs.hourlyRate
        const teamCost = costPerAgent * inputs.teamSize

        setResults({ hoursPerAgent: Math.round(hoursPerAgent), costPerAgent, teamCost })
    }

    const exportToExcel = () => {
        if (!results) return
        const data = { 'Manual Work Cost': { 'Inputs': inputs, 'Results': { 'Hours/Agent/Year': results.hoursPerAgent, 'Cost/Agent (₹)': results.costPerAgent, 'Team Cost (₹)': results.teamCost } } }
        onExport(data, 'Manual_Work_Cost')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info"><Clock size={28} color="#f59e0b" /><h2>Hidden Costs of Manual Work</h2></div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>
            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Your Data</h3>
                    <div className="input-grid">
                        <div className="input-group"><label>Team Size</label><input type="number" value={inputs.teamSize} onChange={(e) => setInputs({ ...inputs, teamSize: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Calls/Day/Agent</label><input type="number" value={inputs.dailyCalls} onChange={(e) => setInputs({ ...inputs, dailyCalls: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Minutes Per Summary</label><input type="number" value={inputs.minutesPerSummary} onChange={(e) => setInputs({ ...inputs, minutesPerSummary: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Working Days/Year</label><input type="number" value={inputs.workingDays} onChange={(e) => setInputs({ ...inputs, workingDays: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Hourly Rate (₹)</label><input type="number" value={inputs.hourlyRate} onChange={(e) => setInputs({ ...inputs, hourlyRate: Number(e.target.value) })} /></div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}><Calculator size={20} /> Calculate Cost</button>
                </div>
                {results && (
                    <div className="calc-results">
                        <h3>💰 Annual Manual Work Cost</h3>
                        <div className="result-highlight danger"><span className="result-label">Total Team Cost</span><span className="result-value">{formatINR(results.teamCost)}</span></div>
                        <div className="result-breakdown">
                            <div className="result-item"><span>Hours Per Agent/Year</span><span>{results.hoursPerAgent}</span></div>
                            <div className="result-item"><span>Cost Per Agent</span><span>{formatINR(results.costPerAgent)}</span></div>
                        </div>
                        <button className="export-btn" onClick={exportToExcel}><Download size={20} /> Export to Excel</button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Calculator 5: Automation Potential Scorecard
function AutomationPotentialCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({ volume: 75, repetitiveness: 85, standardization: 70 })
    const [results, setResults] = useState(null)

    const calculate = () => {
        const score = (inputs.volume * 0.35) + (inputs.repetitiveness * 0.35) + (inputs.standardization * 0.30)
        let tier = score >= 80 ? 'Very High' : score >= 60 ? 'High' : score >= 40 ? 'Moderate' : 'Low'
        setResults({ score: Math.round(score * 10) / 10, tier })
    }

    const exportToExcel = () => {
        if (!results) return
        onExport({ 'Automation Potential': { 'Scores': inputs, 'Result': { 'Overall Score': results.score, 'Tier': results.tier } } }, 'Automation_Potential')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info"><Target size={28} color="#06b6d4" /><h2>Automation Potential Scorecard</h2></div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>
            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📋 Rate Process (0-100)</h3>
                    <div className="input-grid">
                        <div className="input-group">
                            <label>Volume Index (0-100)</label>
                            <input type="number" min="0" max="100" value={inputs.volume} onChange={(e) => setInputs({ ...inputs, volume: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Repetitiveness (0-100)</label>
                            <input type="number" min="0" max="100" value={inputs.repetitiveness} onChange={(e) => setInputs({ ...inputs, repetitiveness: Number(e.target.value) })} />
                        </div>
                        <div className="input-group">
                            <label>Standardization (0-100)</label>
                            <input type="number" min="0" max="100" value={inputs.standardization} onChange={(e) => setInputs({ ...inputs, standardization: Number(e.target.value) })} />
                        </div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}><Calculator size={20} /> Calculate Score</button>
                </div>
                {results && (
                    <div className="calc-results">
                        <h3>🎯 Automation Potential</h3>
                        <div className={`result-highlight ${results.score >= 60 ? 'success' : 'warning'}`}><span className="result-label">Score</span><span className="result-value score">{results.score}/100</span></div>
                        <div className="result-insights"><div className="insight-card"><span className="insight-label">Potential Tier</span><span className="insight-value">{results.tier}</span></div></div>
                        <button className="export-btn" onClick={exportToExcel}><Download size={20} /> Export to Excel</button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Calculator 6: Customer LTV Rescue Tool
function LTVRescueCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({ monthlyRevenue: 10000, monthsActive: 24, grossMargin: 60, cac: 5000, customers: 10000, baseChurn: 5, issueChurn: 7 })
    const [results, setResults] = useState(null)

    const calculate = () => {
        const ltv = (inputs.monthlyRevenue * inputs.monthsActive * (inputs.grossMargin / 100)) - inputs.cac
        const extraChurn = inputs.issueChurn - inputs.baseChurn
        const customersLost = inputs.customers * (extraChurn / 100)
        const monthlyRisk = customersLost * ltv
        const annualRisk = monthlyRisk * 12
        setResults({ ltv, customersLost: Math.round(customersLost), monthlyRisk, annualRisk })
    }

    const exportToExcel = () => {
        if (!results) return
        onExport({ 'LTV Rescue': { 'Inputs': inputs, 'Results': { 'LTV (₹)': results.ltv, 'Customers Lost/Month': results.customersLost, 'Annual Risk (₹)': results.annualRisk } } }, 'LTV_Rescue')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info"><DollarSign size={28} color="#ec4899" /><h2>Customer LTV Rescue Tool</h2></div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>
            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Your Data</h3>
                    <div className="input-grid">
                        <div className="input-group"><label>Monthly Revenue/Customer (₹)</label><input type="number" value={inputs.monthlyRevenue} onChange={(e) => setInputs({ ...inputs, monthlyRevenue: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Avg Months Active</label><input type="number" value={inputs.monthsActive} onChange={(e) => setInputs({ ...inputs, monthsActive: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Gross Margin (%)</label><input type="number" value={inputs.grossMargin} onChange={(e) => setInputs({ ...inputs, grossMargin: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>CAC (₹)</label><input type="number" value={inputs.cac} onChange={(e) => setInputs({ ...inputs, cac: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Total Customers</label><input type="number" value={inputs.customers} onChange={(e) => setInputs({ ...inputs, customers: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Base Churn Rate (%)</label><input type="number" value={inputs.baseChurn} onChange={(e) => setInputs({ ...inputs, baseChurn: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Churn After Issue (%)</label><input type="number" value={inputs.issueChurn} onChange={(e) => setInputs({ ...inputs, issueChurn: Number(e.target.value) })} /></div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}><Calculator size={20} /> Calculate Risk</button>
                </div>
                {results && (
                    <div className="calc-results">
                        <h3>⚠️ Revenue at Risk</h3>
                        <div className="result-highlight danger"><span className="result-label">Annual Revenue at Risk</span><span className="result-value">{formatINR(results.annualRisk)}</span></div>
                        <div className="result-breakdown">
                            <div className="result-item"><span>Customer LTV</span><span>{formatINR(results.ltv)}</span></div>
                            <div className="result-item"><span>Extra Customers Lost/Month</span><span>{results.customersLost}</span></div>
                        </div>
                        <button className="export-btn" onClick={exportToExcel}><Download size={20} /> Export to Excel</button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Calculator 7: Scalability Stress Test
function ScalabilityCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({ teamSize: 50, callsPerAgent: 20, workingDays: 245, currentDemand: 200000, growthRate: 10 })
    const [results, setResults] = useState(null)

    const calculate = () => {
        const capacity = inputs.teamSize * inputs.callsPerAgent * inputs.workingDays
        const buffer = capacity - inputs.currentDemand
        let breakMonth = 0
        let demand = inputs.currentDemand
        while (demand < capacity && breakMonth < 24) {
            breakMonth++
            demand = demand * (1 + inputs.growthRate / 100)
        }
        setResults({ capacity, buffer, breakMonth: breakMonth >= 24 ? 'Not in 24 months' : `Month ${breakMonth}` })
    }

    const exportToExcel = () => {
        if (!results) return
        onExport({ 'Scalability Test': { 'Inputs': inputs, 'Results': { 'Current Capacity': results.capacity, 'Buffer': results.buffer, 'Breaking Point': results.breakMonth } } }, 'Scalability_Test')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info"><TrendingUp size={28} color="#14b8a6" /><h2>Scalability Stress Test</h2></div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>
            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Your Data</h3>
                    <div className="input-grid">
                        <div className="input-group"><label>Team Size</label><input type="number" value={inputs.teamSize} onChange={(e) => setInputs({ ...inputs, teamSize: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Calls/Agent/Day</label><input type="number" value={inputs.callsPerAgent} onChange={(e) => setInputs({ ...inputs, callsPerAgent: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Working Days/Year</label><input type="number" value={inputs.workingDays} onChange={(e) => setInputs({ ...inputs, workingDays: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Current Annual Demand</label><input type="number" value={inputs.currentDemand} onChange={(e) => setInputs({ ...inputs, currentDemand: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Monthly Growth Rate (%)</label><input type="number" value={inputs.growthRate} onChange={(e) => setInputs({ ...inputs, growthRate: Number(e.target.value) })} /></div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}><Calculator size={20} /> Run Stress Test</button>
                </div>
                {results && (
                    <div className="calc-results">
                        <h3>📈 Scalability Results</h3>
                        <div className="result-highlight warning"><span className="result-label">Breaking Point</span><span className="result-value">{results.breakMonth}</span></div>
                        <div className="result-breakdown">
                            <div className="result-item"><span>Current Capacity</span><span>{results.capacity.toLocaleString()} calls</span></div>
                            <div className="result-item"><span>Buffer Available</span><span>{results.buffer.toLocaleString()} calls</span></div>
                        </div>
                        <button className="export-btn" onClick={exportToExcel}><Download size={20} /> Export to Excel</button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Calculator 8: Process Bottleneck Identifier
function BottleneckCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({ frequency: 5000, duration: 2, hourlyRate: 200, errorRate: 15, reworkTime: 1, escalationCost: 500 })
    const [results, setResults] = useState(null)

    const calculate = () => {
        const baseCost = inputs.frequency * inputs.duration * inputs.hourlyRate
        const errorCost = inputs.frequency * (inputs.errorRate / 100) * inputs.reworkTime * inputs.hourlyRate
        const escalationCost = inputs.frequency * (inputs.errorRate / 100) * inputs.escalationCost
        const totalCost = baseCost + errorCost + escalationCost
        setResults({ baseCost, errorCost, escalationCost, totalCost })
    }

    const exportToExcel = () => {
        if (!results) return
        onExport({ 'Bottleneck Analysis': { 'Inputs': inputs, 'Results': { 'Base Cost': results.baseCost, 'Error Cost': results.errorCost, 'Escalation Cost': results.escalationCost, 'Total Cost': results.totalCost } } }, 'Bottleneck_Analysis')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info"><Workflow size={28} color="#f97316" /><h2>Process Bottleneck Identifier</h2></div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>
            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Process Data</h3>
                    <div className="input-grid">
                        <div className="input-group"><label>Annual Frequency</label><input type="number" value={inputs.frequency} onChange={(e) => setInputs({ ...inputs, frequency: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Duration (hours)</label><input type="number" value={inputs.duration} onChange={(e) => setInputs({ ...inputs, duration: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Hourly Rate (₹)</label><input type="number" value={inputs.hourlyRate} onChange={(e) => setInputs({ ...inputs, hourlyRate: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Error Rate (%)</label><input type="number" value={inputs.errorRate} onChange={(e) => setInputs({ ...inputs, errorRate: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Rework Time (hours)</label><input type="number" value={inputs.reworkTime} onChange={(e) => setInputs({ ...inputs, reworkTime: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Escalation Cost (₹)</label><input type="number" value={inputs.escalationCost} onChange={(e) => setInputs({ ...inputs, escalationCost: Number(e.target.value) })} /></div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}><Calculator size={20} /> Identify Cost</button>
                </div>
                {results && (
                    <div className="calc-results">
                        <h3>🔍 Bottleneck Cost</h3>
                        <div className="result-highlight danger"><span className="result-label">Total Annual Cost</span><span className="result-value">{formatINR(results.totalCost)}</span></div>
                        <div className="result-breakdown">
                            <div className="result-item"><span>Base Processing Cost</span><span>{formatINR(results.baseCost)}</span></div>
                            <div className="result-item"><span>Error/Rework Cost</span><span>{formatINR(results.errorCost)}</span></div>
                            <div className="result-item"><span>Escalation Cost</span><span>{formatINR(results.escalationCost)}</span></div>
                        </div>
                        <button className="export-btn" onClick={exportToExcel}><Download size={20} /> Export to Excel</button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Calculator 9: AHT Reduction Planner
function AHTReductionCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({ teamSize: 50, currentCallsPerDay: 20, targetCallsPerDay: 30, workingDays: 245, revenuePerCall: 200 })
    const [results, setResults] = useState(null)

    const calculate = () => {
        const additionalCalls = (inputs.targetCallsPerDay - inputs.currentCallsPerDay) * inputs.teamSize * inputs.workingDays
        const extraRevenue = additionalCalls * inputs.revenuePerCall
        const throughputIncrease = ((inputs.targetCallsPerDay - inputs.currentCallsPerDay) / inputs.currentCallsPerDay) * 100
        setResults({ additionalCalls, extraRevenue, throughputIncrease: Math.round(throughputIncrease) })
    }

    const exportToExcel = () => {
        if (!results) return
        onExport({ 'AHT Reduction': { 'Inputs': inputs, 'Results': { 'Additional Calls/Year': results.additionalCalls, 'Extra Revenue (₹)': results.extraRevenue, 'Throughput Increase (%)': results.throughputIncrease } } }, 'AHT_Reduction')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info"><Clock size={28} color="#84cc16" /><h2>AHT Reduction Planner</h2></div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>
            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Your Data</h3>
                    <div className="input-grid">
                        <div className="input-group"><label>Team Size</label><input type="number" value={inputs.teamSize} onChange={(e) => setInputs({ ...inputs, teamSize: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Current Calls/Agent/Day</label><input type="number" value={inputs.currentCallsPerDay} onChange={(e) => setInputs({ ...inputs, currentCallsPerDay: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Target Calls/Agent/Day</label><input type="number" value={inputs.targetCallsPerDay} onChange={(e) => setInputs({ ...inputs, targetCallsPerDay: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Working Days/Year</label><input type="number" value={inputs.workingDays} onChange={(e) => setInputs({ ...inputs, workingDays: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Revenue Per Call (₹)</label><input type="number" value={inputs.revenuePerCall} onChange={(e) => setInputs({ ...inputs, revenuePerCall: Number(e.target.value) })} /></div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}><Calculator size={20} /> Calculate Gains</button>
                </div>
                {results && (
                    <div className="calc-results">
                        <h3>⚡ AHT Reduction Impact</h3>
                        <div className="result-highlight success"><span className="result-label">Extra Revenue Potential</span><span className="result-value">{formatINR(results.extraRevenue)}</span></div>
                        <div className="result-breakdown">
                            <div className="result-item"><span>Additional Calls/Year</span><span>{results.additionalCalls.toLocaleString()}</span></div>
                            <div className="result-item"><span>Throughput Increase</span><span>{results.throughputIncrease}%</span></div>
                        </div>
                        <button className="export-btn" onClick={exportToExcel}><Download size={20} /> Export to Excel</button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Calculator 10: SLA Failure Cost Calculator
function SLAFailureCalculator({ onClose, onExport }) {
    const [inputs, setInputs] = useState({ annualRevenue: 100000000, penaltyRate: 5, customers: 100, ltv: 139000, churnIncrease: 5, escalationCost: 600000 })
    const [results, setResults] = useState(null)

    const calculate = () => {
        const monthlyRevenue = inputs.annualRevenue / 12
        const annualPenalty = monthlyRevenue * (inputs.penaltyRate / 100) * 12
        const customersLost = inputs.customers * (inputs.churnIncrease / 100)
        const churnCost = customersLost * inputs.ltv * 12
        const totalImpact = annualPenalty + churnCost + inputs.escalationCost
        setResults({ annualPenalty, customersLost, churnCost, totalImpact })
    }

    const exportToExcel = () => {
        if (!results) return
        onExport({ 'SLA Failure Cost': { 'Inputs': inputs, 'Results': { 'Annual Penalty (₹)': results.annualPenalty, 'Churn Cost (₹)': results.churnCost, 'Total Impact (₹)': results.totalImpact } } }, 'SLA_Failure_Cost')
    }

    return (
        <div className="calculator-modal">
            <div className="calculator-header">
                <div className="calc-header-info"><AlertTriangle size={28} color="#dc2626" /><h2>SLA Failure Cost Calculator</h2></div>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>
            </div>
            <div className="calculator-body">
                <div className="calc-inputs">
                    <h3>📊 Enter Your Data</h3>
                    <div className="input-grid">
                        <div className="input-group"><label>Annual Revenue (₹)</label><input type="number" value={inputs.annualRevenue} onChange={(e) => setInputs({ ...inputs, annualRevenue: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>SLA Penalty Rate (%)</label><input type="number" value={inputs.penaltyRate} onChange={(e) => setInputs({ ...inputs, penaltyRate: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Total Customers</label><input type="number" value={inputs.customers} onChange={(e) => setInputs({ ...inputs, customers: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Customer LTV (₹)</label><input type="number" value={inputs.ltv} onChange={(e) => setInputs({ ...inputs, ltv: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Churn Increase (%)</label><input type="number" value={inputs.churnIncrease} onChange={(e) => setInputs({ ...inputs, churnIncrease: Number(e.target.value) })} /></div>
                        <div className="input-group"><label>Escalation Costs (₹)</label><input type="number" value={inputs.escalationCost} onChange={(e) => setInputs({ ...inputs, escalationCost: Number(e.target.value) })} /></div>
                    </div>
                    <button className="calculate-btn" onClick={calculate}><Calculator size={20} /> Calculate Impact</button>
                </div>
                {results && (
                    <div className="calc-results">
                        <h3>🚨 SLA Failure Impact</h3>
                        <div className="result-highlight danger"><span className="result-label">Total Annual Impact</span><span className="result-value">{formatINR(results.totalImpact)}</span></div>
                        <div className="result-breakdown">
                            <div className="result-item"><span>Direct SLA Penalties</span><span>{formatINR(results.annualPenalty)}</span></div>
                            <div className="result-item"><span>Customer Churn Cost</span><span>{formatINR(results.churnCost)}</span></div>
                        </div>
                        <button className="export-btn" onClick={exportToExcel}><Download size={20} /> Export to Excel</button>
                    </div>
                )}
            </div>
        </div>
    )
}

// Main Calculators Section Component
export default function CalculatorsSection() {
    const [activeCalculator, setActiveCalculator] = useState(null)

    const exportToExcel = (data, filename) => {
        // Create workbook
        const wb = XLSX.utils.book_new()
        const wsData = []
        const headerRowIndices = [] // Track which rows are headers for styling
        const sectionRowIndices = [] // Track section headers

        // Build Excel data with proper structure
        for (const section in data) {
            // Add main section header (like "AI Readiness Diagnostic")
            sectionRowIndices.push(wsData.length)
            wsData.push([{ v: section, t: 's' }, ''])
            wsData.push(['', '']) // Empty row for spacing

            for (const group in data[section]) {
                // Add group header with blue background (like "Process Scores")
                headerRowIndices.push(wsData.length)
                wsData.push([{ v: group, t: 's' }, ''])

                // Add data rows with key-value pairs
                for (const key in data[section][group]) {
                    const value = data[section][group][key]
                    const formattedValue = typeof value === 'number' ?
                        (value >= 100000 ? `₹${value.toLocaleString('en-IN')}` : String(value)) : String(value)
                    wsData.push([{ v: key, t: 's' }, { v: formattedValue, t: 's' }])
                }
                wsData.push(['', '']) // Empty row between groups
            }
        }

        // Create worksheet from data
        const ws = XLSX.utils.aoa_to_sheet(wsData.map(row => row.map(cell =>
            typeof cell === 'object' ? cell.v : cell
        )))

        // Set column widths for better readability
        ws['!cols'] = [
            { wch: 40 }, // Column A - Labels
            { wch: 30 }  // Column B - Values
        ]

        // Define styles
        const sectionStyle = {
            font: { bold: true, sz: 14, color: { rgb: "1E3A5F" } },
            fill: { fgColor: { rgb: "E7E6E6" } },
            alignment: { horizontal: "left", vertical: "center", wrapText: true },
            border: {
                top: { style: "thin", color: { rgb: "000000" } },
                bottom: { style: "thin", color: { rgb: "000000" } },
                left: { style: "thin", color: { rgb: "000000" } },
                right: { style: "thin", color: { rgb: "000000" } }
            }
        }

        const headerStyle = {
            font: { bold: true, sz: 11, color: { rgb: "FFFFFF" } },
            fill: { fgColor: { rgb: "4472C4" } }, // Blue background like in image
            alignment: { horizontal: "left", vertical: "center", wrapText: true },
            border: {
                top: { style: "thin", color: { rgb: "000000" } },
                bottom: { style: "thin", color: { rgb: "000000" } },
                left: { style: "thin", color: { rgb: "000000" } },
                right: { style: "thin", color: { rgb: "000000" } }
            }
        }

        const dataStyle = {
            font: { sz: 10 },
            alignment: { horizontal: "left", vertical: "center", wrapText: true },
            border: {
                top: { style: "thin", color: { rgb: "D0D0D0" } },
                bottom: { style: "thin", color: { rgb: "D0D0D0" } },
                left: { style: "thin", color: { rgb: "D0D0D0" } },
                right: { style: "thin", color: { rgb: "D0D0D0" } }
            }
        }

        // Apply styles to all cells
        const range = XLSX.utils.decode_range(ws['!ref'] || 'A1')
        for (let R = range.s.r; R <= range.e.r; R++) {
            for (let C = range.s.c; C <= range.e.c; C++) {
                const cellRef = XLSX.utils.encode_cell({ r: R, c: C })
                if (!ws[cellRef]) {
                    ws[cellRef] = { v: '', t: 's' }
                }

                // Check if this is a section header row
                if (sectionRowIndices.includes(R)) {
                    ws[cellRef].s = sectionStyle
                }
                // Check if this is a group header row (blue background)
                else if (headerRowIndices.includes(R)) {
                    ws[cellRef].s = headerStyle
                }
                // Regular data row
                else {
                    ws[cellRef].s = dataStyle
                }
            }
        }

        // Set row heights for better text wrap visibility
        ws['!rows'] = wsData.map((_, idx) => {
            if (sectionRowIndices.includes(idx)) {
                return { hpt: 25 } // Taller for section headers
            } else if (headerRowIndices.includes(idx)) {
                return { hpt: 22 } // Standard header height
            }
            return { hpt: 18 } // Standard data row height
        })

        // Add worksheet to workbook
        XLSX.utils.book_append_sheet(wb, ws, 'Report')

        // Generate Excel file and trigger download
        const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
        const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.xlsx`)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    }

    const renderCalculator = () => {
        switch (activeCalculator) {
            case 'attrition':
                return <AttritionCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'ai-readiness':
                return <AIReadinessCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'ticket-deflection':
                return <TicketDeflectionCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'manual-work':
                return <ManualWorkCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'automation-potential':
                return <AutomationPotentialCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'ltv-rescue':
                return <LTVRescueCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'scalability':
                return <ScalabilityCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'bottleneck':
                return <BottleneckCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'aht-reduction':
                return <AHTReductionCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            case 'sla-failure':
                return <SLAFailureCalculator onClose={() => setActiveCalculator(null)} onExport={exportToExcel} />
            default:
                return null
        }
    }

    return (
        <section className="calculators-section">
            <motion.div
                className="section-header"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
            >
                <FileSpreadsheet className="section-icon" />
                <h2>📊 ROI Calculators</h2>
                <p className="section-subtitle">Calculate your hidden costs & savings potential</p>
            </motion.div>

            <div className="calculators-grid">
                {CALCULATORS.map((calc, index) => (
                    <motion.div
                        key={calc.id}
                        className="calculator-card"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 + index * 0.1 }}
                        whileHover={{ y: -8, boxShadow: `0 20px 50px ${calc.color}30` }}
                        onClick={() => setActiveCalculator(calc.id)}
                    >
                        <div className="calc-card-icon" style={{ background: `${calc.color}20`, color: calc.color }}>
                            <calc.icon size={32} />
                        </div>
                        <h4>{calc.title}</h4>
                        <p>{calc.subtitle}</p>
                        <div className="calc-impact" style={{ color: calc.color }}>
                            Typical Impact: {calc.impact}
                        </div>
                        <div className="calc-cta">
                            <span>Calculate Now</span>
                            <ChevronRight size={18} />
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Calculator Modal */}
            <AnimatePresence>
                {activeCalculator && (
                    <motion.div
                        className="calculator-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setActiveCalculator(null)}
                    >
                        <motion.div
                            className="calculator-container"
                            initial={{ opacity: 0, scale: 0.9, y: 50 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 50 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            {renderCalculator()}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </section>
    )
}
