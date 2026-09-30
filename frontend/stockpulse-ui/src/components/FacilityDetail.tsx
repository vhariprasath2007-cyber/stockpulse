import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

interface FacilityDetailProps {
  facilityId: string;
  onRecommendClick: (itemId: string, facilityId: string) => void;
}

interface StockItem {
  item_id: string;
  item_name: string;
  unit: string;
  current_stock: number;
  daily_consumption: number;
  days_remaining: number;
  lead_time_days: number;
  risk_level: string;
}

interface FacilityDetailData {
  facility_id: string;
  facility_name: string;
  items: StockItem[];
}

const getRiskClass = (risk: string) => {
  switch (risk) {
    case 'critical': return 'critical';
    case 'watch': return 'watch';
    default: return 'normal';
  }
};

const getRunwayWidth = (days: number, leadTime: number) => {
  const maxDays = leadTime * 3;
  return Math.min(100, Math.max(0, (days / maxDays) * 100));
};

export default function FacilityDetail({ facilityId, onRecommendClick }: FacilityDetailProps) {
  const [data, setData] = useState<FacilityDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/facilities/${facilityId}/stock`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch facility stock');
        return res.json();
      })
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [facilityId]);

  const handleSimulate = async (itemId: string) => {
    setSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, facility_id: facilityId, delay_days: 3 })
      });
      if (!res.ok) throw new Error('Simulation failed');
      const result = await res.json();
      setSimulationResult(result);
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return <div className="loading"><div className="spinner"></div>Loading facility details...</div>;
  }

  if (error || !data) {
    return (
      <div className="card">
        <div className="card-body" style={{textAlign: 'center', color: 'var(--color-critical)'}}>
          Error loading facility: {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="detail-header">
        <div className="detail-title">
          <h2>{data.facility_name}</h2>
          <p>Facility ID: {data.facility_id}</p>
        </div>
      </div>

      {simulationResult && (
        <div className="simulation-result">
          <div className="sim-header">
            <span className="sim-title">Disruption Simulation: 3-Day Supplier Delay</span>
            <button className="btn btn-secondary btn-sm" onClick={() => setSimulationResult(null)}>Close</button>
          </div>
          <div className="sim-before-after">
            <div className="sim-column">
              <h4>Before</h4>
              <div className={`sim-risk ${simulationResult.original_risk}`}>{simulationResult.original_risk.toUpperCase()}</div>
              <p style={{fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '4px'}}>
                Lead time: {simulationResult.original_lead_time} days
              </p>
            </div>
            <div className="sim-column">
              <h4>After (with delay)</h4>
              <div className={`sim-risk ${simulationResult.simulated_risk}`}>{simulationResult.simulated_risk.toUpperCase()}</div>
              <p style={{fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '4px'}}>
                Lead time: {simulationResult.simulated_lead_time} days
              </p>
            </div>
          </div>
          <p style={{fontSize: '0.85rem', marginTop: '12px', color: 'var(--color-text-muted)'}}>
            Days remaining unchanged at {simulationResult.original_days_remaining.toFixed(1)} days — risk increases because replenishment takes longer.
          </p>
        </div>
      )}

      <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
        {data.items.map(item => (
          <div key={item.item_id} className="card item-detail-card">
            <div className="item-detail-header">
              <span className="item-detail-name">{item.item_name} ({item.unit})</span>
              <div className="item-detail-meta">
                <span className={`status-badge ${item.risk_level}`}>{item.risk_level.toUpperCase()}</span>
                <span>Stock: {item.current_stock} {item.unit}</span>
                <span>Avg/day: {item.daily_consumption.toFixed(1)}</span>
              </div>
            </div>
            <div className="item-detail-body">
              <div className="stat">
                <span className="stat-label">Current Stock</span>
                <span className="stat-value">{item.current_stock}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Daily Consumption</span>
                <span className="stat-value">{item.daily_consumption.toFixed(1)}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Days Remaining</span>
                <span className={`stat-value ${getRiskClass(item.risk_level)}`}>{item.days_remaining.toFixed(1)}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Lead Time</span>
                <span className="stat-value">{item.lead_time_days} days</span>
              </div>
              <div className="progress-container">
                <div className="progress-bar">
                  <div
                    className={`progress-fill ${getRiskClass(item.risk_level)}`}
                    style={{width: `${getRunwayWidth(item.days_remaining, item.lead_time_days)}%`}}
                  ></div>
                </div>
                <p style={{fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '4px'}}>
                  Runway vs {item.lead_time_days * 3} days (3× lead time)
                </p>
              </div>
              {item.risk_level === 'critical' && (
                <div style={{marginTop: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap'}}>
                  <button
                    className="btn btn-primary"
                    onClick={() => onRecommendClick(item.item_id, facilityId)}
                    disabled={simulating}
                  >
                    Get Transfer Recommendation
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleSimulate(item.item_id)}
                    disabled={simulating}
                  >
                    {simulating ? 'Simulating...' : 'Simulate 3-Day Delay'}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}