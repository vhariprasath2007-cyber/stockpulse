import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

interface RecommendationPanelProps {
  itemId: string;
  facilityId: string;
  onClose: () => void;
  onApply: () => void;
}

interface Recommendation {
  item_id: string;
  item_name: string;
  requesting_facility_id: string;
  requesting_facility_name: string;
  source_facility_id: string;
  source_facility_name: string;
  quantity: number;
  distance_km: number;
  requester_days_before: number;
  requester_days_after: number;
  donor_days_before: number;
  donor_days_after: number;
  donor_safe: boolean;
}

export default function RecommendationPanel({ itemId, facilityId, onClose, onApply }: RecommendationPanelProps) {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [explaining, setExplaining] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/transfer/recommend?item_id=${itemId}&facility_id=${facilityId}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to get recommendation');
        return res.json();
      })
      .then(data => {
        if (data.recommendation) {
          setRecommendation(data.recommendation);
        }
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });
  }, [itemId, facilityId]);

  const handleExplain = async () => {
    if (!recommendation) return;
    setExplaining(true);
    try {
      const res = await fetch(`${API_BASE}/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          facility: recommendation.requesting_facility_name,
          item: recommendation.item_name,
          days_remaining: recommendation.requester_days_before,
          risk_level: 'critical',
          recommended_transfer: {
            from_facility: recommendation.source_facility_name,
            quantity: recommendation.quantity,
            distance_km: recommendation.distance_km
          },
          post_transfer_days_remaining: recommendation.requester_days_after
        })
      });
      if (!res.ok) throw new Error('Failed to get explanation');
      const data = await res.json();
      setExplanation(data.explanation);
    } catch (err) {
      setExplanation('Unable to generate explanation at this time.');
    } finally {
      setExplaining(false);
    }
  };

  const handleApply = async () => {
    if (!recommendation) return;
    setApplying(true);
    try {
      const res = await fetch(`${API_BASE}/transfer/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_id: recommendation.item_id,
          source_facility_id: recommendation.source_facility_id,
          destination_facility_id: recommendation.requesting_facility_id,
          quantity: recommendation.quantity
        })
      });
      if (!res.ok) throw new Error('Failed to apply transfer');
      await res.json();
      onApply();
    } catch (err: Error) {
      setError(err.message);
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="card recommendation-panel" style={{position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', right: 'auto', maxWidth: '800px', width: 'calc(100% - 48px)', maxHeight: '90vh', overflowY: 'auto', zIndex: 100, boxShadow: 'var(--shadow-lg)'}}>
        <div className="loading"><div className="spinner"></div>Loading recommendation...</div>
      </div>
    );
  }

  if (error && !recommendation) {
    return (
      <div className="card recommendation-panel" style={{position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', right: 'auto', maxWidth: '800px', width: 'calc(100% - 48px)', maxHeight: '90vh', overflowY: 'auto', zIndex: 100, boxShadow: 'var(--shadow-lg)'}}>
        <div className="card-body" style={{textAlign: 'center', color: 'var(--color-critical)'}}>
          <p>Error: {error}</p>
          <button className="btn btn-secondary" style={{marginTop: '16px'}} onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (!recommendation) {
    return (
      <div className="card recommendation-panel" style={{position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', right: 'auto', maxWidth: '800px', width: 'calc(100% - 48px)', maxHeight: '90vh', overflowY: 'auto', zIndex: 100, boxShadow: 'var(--shadow-lg)'}}>
        <div className="card-body" style={{textAlign: 'center'}}>
          <p>No safe transfer recommendation available.</p>
          <button className="btn btn-secondary" style={{marginTop: '16px'}} onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  return (
    <div className="card recommendation-panel" style={{position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', right: 'auto', maxWidth: '800px', width: 'calc(100% - 48px)', maxHeight: '90vh', overflowY: 'auto', zIndex: 100, boxShadow: 'var(--shadow-lg)'}}>
      <div className="recommendation-header">
        <span className="recommendation-title">Transfer Recommendation: {recommendation.item_name}</span>
        <button className="btn btn-secondary btn-sm" style={{background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none'}} onClick={onClose}>✕</button>
      </div>
      <div className="recommendation-body" style={{paddingBottom: '24px'}}>
        <div className="reco-section">
          <h4>Requesting Facility</h4>
          <div className="reco-row"><span className="reco-label">Facility</span><span className="reco-value">{recommendation.requesting_facility_name}</span></div>
          <div className="reco-row"><span className="reco-label">Days Before Transfer</span><span className="reco-value" style={{color: 'var(--color-critical)'}}>{recommendation.requester_days_before.toFixed(1)}</span></div>
          <div className="reco-row"><span className="reco-label">Days After Transfer</span><span className="reco-value" style={{color: 'var(--color-normal)'}}>{recommendation.requester_days_after.toFixed(1)}</span></div>
        </div>
        <div className="reco-section">
          <h4>Donor Facility</h4>
          <div className="reco-row"><span className="reco-label">Facility</span><span className="reco-value">{recommendation.source_facility_name}</span></div>
          <div className="reco-row"><span className="reco-label">Distance</span><span className="reco-value">{recommendation.distance_km.toFixed(1)} km</span></div>
          <div className="reco-row"><span className="reco-label">Days Before Transfer</span><span className="reco-value">{recommendation.donor_days_before.toFixed(1)}</span></div>
          <div className="reco-row"><span className="reco-label">Days After Transfer</span><span className="reco-value">{recommendation.donor_days_after.toFixed(1)}</span></div>
          <div className="reco-row"><span className="reco-label">Cascade Safe</span><span className="reco-value" style={{color: recommendation.donor_safe ? 'var(--color-normal)' : 'var(--color-critical)'}}>{recommendation.donor_safe ? 'Yes' : 'No'}</span></div>
        </div>
        <div className="reco-section" style={{gridColumn: '1 / -1'}}>
          <h4>Transfer Details</h4>
          <div className="reco-row"><span className="reco-label">Quantity</span><span className="reco-value">{recommendation.quantity} units</span></div>
          <div className="reco-row"><span className="reco-label">Item</span><span className="reco-value">{recommendation.item_name}</span></div>
        </div>
        <div className="reco-actions">
          <button className="btn btn-secondary" onClick={handleExplain} disabled={explaining}>
            {explaining ? 'Explaining...' : 'Explain'}
          </button>
          <button className="btn btn-primary" onClick={handleApply} disabled={applying}>
            {applying ? 'Applying...' : 'Apply Transfer'}
          </button>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        </div>
        {explanation && (
          <div className="explanation-box">
            <div className="explanation-label">AI Explanation</div>
            <div className="explanation-text">{explanation}</div>
          </div>
        )}
      </div>
    </div>
  );
}