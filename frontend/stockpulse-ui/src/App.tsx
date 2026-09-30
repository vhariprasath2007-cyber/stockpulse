import { useState, useEffect } from 'react';
import FacilityOverview from './components/FacilityOverview';
import FacilityDetail from './components/FacilityDetail';
import RecommendationPanel from './components/RecommendationPanel';
import GeminiQuery from './components/GeminiQuery';
import './index.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [view, setView] = useState<'overview' | 'detail'>('overview');
  const [selectedFacility, setSelectedFacility] = useState<string | null>(null);
  const [showRecommendation, setShowRecommendation] = useState<{itemId: string, facilityId: string} | null>(null);
  const [showSimulation, setShowSimulation] = useState<{itemId: string, facilityId: string} | null>(null);

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>StockPulse</h1>
          <p className="subtitle">Medicine & Vaccine Stockout Prevention</p>
        </div>
        <div style={{display: 'flex', gap: '12px', alignItems: 'center'}}>
          <span style={{fontSize: '0.85rem', color: 'var(--color-text-muted)'}}>
            {view === 'detail' && selectedFacility && (
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => { setView('overview'); setSelectedFacility(null); }}
              >
                ← All Facilities
              </button>
            )}
          </span>
        </div>
      </header>

      {view === 'overview' && (
        <FacilityOverview 
          onFacilityClick={(facilityId) => { setSelectedFacility(facilityId); setView('detail'); }}
        />
      )}

      {view === 'detail' && selectedFacility && (
        <FacilityDetail 
          facilityId={selectedFacility}
          onRecommendClick={(itemId, facilityId) => setShowRecommendation({itemId, facilityId})}
          onSimulateClick={(itemId, facilityId) => setShowSimulation({itemId, facilityId})}
        />
      )}

      {showRecommendation && (
        <RecommendationPanel
          itemId={showRecommendation.itemId}
          facilityId={showRecommendation.facilityId}
          onClose={() => setShowRecommendation(null)}
          onApply={() => setShowRecommendation(null)}
        />
      )}

      {showSimulation && (
        <GeminiQuery
          itemId={showSimulation.itemId}
          facilityId={showSimulation.facilityId}
          onClose={() => setShowSimulation(null)}
        />
      )}
    </div>
  );
}

export default App;