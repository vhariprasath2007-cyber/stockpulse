import { useState, useEffect } from 'react';
import { API_BASE } from '../config';

interface Facility {
  facility_id: string;
  name: string;
  district: string;
  type: string;
  latitude: number;
  longitude: number;
  items: Array<{
    item_id: string;
    item_name: string;
    unit: string;
    current_stock: number;
    daily_consumption: number;
    days_remaining: number;
    lead_time_days: number;
    risk_level: string;
  }>;
  overall_risk: string;
}

interface FacilityOverviewProps {
  onFacilityClick: (facilityId: string) => void;
}

export default function FacilityOverview({ onFacilityClick }: FacilityOverviewProps) {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/facilities`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch facilities');
        return res.json();
      })
      .then(data => {
        setFacilities(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

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

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        Loading facilities...
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body" style={{textAlign: 'center', color: 'var(--color-critical)'}}>
          Error loading facilities: {error}
          <button className="btn btn-primary" style={{marginTop: '16px'}} onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (facilities.length === 0) {
    return (
      <div className="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
        </svg>
        <p>No facilities found</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{marginBottom: '16px', fontSize: '0.9rem', color: 'var(--color-text-muted)'}}>
        {facilities.length} facilities monitored
      </div>
      <div className="facility-grid">
        {facilities.map(facility => (
          <div
            key={facility.facility_id}
            className={`card facility-card ${getRiskClass(facility.overall_risk)}`}
            onClick={() => onFacilityClick(facility.facility_id)}
            style={{cursor: 'pointer'}}
          >
            <div className="card-body">
              <div className="facility-card-header">
                <div>
                  <div className="facility-name">{facility.name}</div>
                  <div className="facility-district">{facility.district} • {facility.type}</div>
                </div>
                <span className="facility-type">{facility.type}</span>
              </div>
              <div className="facility-items">
                {facility.items.map(item => (
                  <div key={item.item_id} className="item-row">
                    <div className="item-info">
                      <span className="item-name">{item.item_name}</span>
                      <span className="item-meta">
                        {item.current_stock} {item.unit} • {item.daily_consumption.toFixed(1)}/{item.unit}/day
                      </span>
                    </div>
                    <div className="item-status">
                      <div className="runway-bar">
                        <div
                          className={`runway-fill ${getRiskClass(item.risk_level)}`}
                          style={{width: `${getRunwayWidth(item.days_remaining, item.lead_time_days)}%`}}
                        ></div>
                      </div>
                      <span className={`status-badge ${item.risk_level}`}>{item.risk_level}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}