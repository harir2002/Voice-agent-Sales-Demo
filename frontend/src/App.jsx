import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import DemoPage from './components/DemoPage'
import VoiceAgentPage from './components/VoiceAgentPage'
import TwilioDemo from './components/TwilioDemo'
import CallDashboard from './components/CallDashboard'
import CalculatorsSection from './components/CalculatorsSection'
import SarvamPlayground from './components/SarvamPlayground'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          {/* Main demo page with sidebar */}
          <Route path="/" element={<DemoPage />} />

          {/* Direct links to individual sector demos */}
          <Route path="/demo/banking" element={<DemoPage initialSector="banking" />} />
          <Route path="/demo/financial" element={<DemoPage initialSector="financial" />} />
          <Route path="/demo/insurance" element={<DemoPage initialSector="insurance" />} />
          <Route path="/demo/bpo" element={<DemoPage initialSector="bpo" />} />
          <Route path="/demo/healthcare-appt" element={<DemoPage initialSector="healthcare_appt" />} />
          <Route path="/demo/healthcare-patient" element={<DemoPage initialSector="healthcare_patient" />} />

          {/* Direct links to phone calls for each sector */}
          <Route path="/phone/banking" element={<DemoPage initialView="phone" initialPhoneSector="banking" />} />
          <Route path="/phone/financial" element={<DemoPage initialView="phone" initialPhoneSector="financial" />} />
          <Route path="/phone/insurance" element={<DemoPage initialView="phone" initialPhoneSector="insurance" />} />
          <Route path="/phone/bpo" element={<DemoPage initialView="phone" initialPhoneSector="bpo" />} />
          <Route path="/phone/healthcare-appt" element={<DemoPage initialView="phone" initialPhoneSector="healthcare_appt" />} />
          <Route path="/phone/healthcare-patient" element={<DemoPage initialView="phone" initialPhoneSector="healthcare_patient" />} />

          {/* Other quick action routes */}
          <Route path="/analytics" element={<DemoPage initialView="analytics" />} />
          <Route path="/calculators" element={<DemoPage initialView="calculators" />} />
          <Route path="/playground" element={<DemoPage initialView="playground" />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
