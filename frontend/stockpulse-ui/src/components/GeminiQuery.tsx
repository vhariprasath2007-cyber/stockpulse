import { useState, useEffect, type FormEvent } from 'react';

const API_BASE = 'http://localhost:8000';

interface GeminiQueryProps {
  itemId: string;
  facilityId: string;
}

export default function GeminiQuery({ itemId, facilityId }: GeminiQueryProps) {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [forecast, setForecast] = useState<any>(null);

  useEffect(() => {
    fetch(`${API_BASE}/forecast/${itemId}/${facilityId}`)
      .then(res => res.json())
      .then(setForecast)
      .catch(console.error);
  }, [itemId, facilityId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !forecast) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          facility: forecast.item_name,
          item: forecast.item_name,
          days_remaining: forecast.days_remaining,
          risk_level: forecast.risk_level,
          recommended_transfer: null,
          post_transfer_days_remaining: null
        })
      });
      if (!res.ok) throw new Error('Failed to get explanation');
      const data = await res.json();
      setResponse(data.explanation);
    } catch (err: unknown) {
      setResponse('Unable to generate explanation at this time.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card gemini-query" style={{maxWidth: '600px', margin: '0 auto'}}>
      <div className="card-header">Ask StockPulse</div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <textarea
            className="query-input"
            rows={3}
            placeholder="e.g., Why is PHC Madurai North at risk for ORS? What would a transfer do?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <button className="btn btn-primary" type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </form>
        {response && (
          <div className="explanation-box" style={{marginTop: '16px'}}>
            <div className="explanation-label">Answer</div>
            <div className="explanation-text">{response}</div>
          </div>
        )}
      </div>
    </div>
  );
}