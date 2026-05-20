import { useState } from 'react'
import { api } from '../api'
type ModelType = 'linear' | 'random_forest'

export default function Train(){
  const [model, setModel] = useState<ModelType>('linear')
  const [nTrees, setNTrees] = useState(200)
  const [maxDepth, setMaxDepth] = useState<number | ''>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [expId, setExpId] = useState<number | null>(null)

  async function onTrain(){
    setLoading(true); setError(null); setMetrics(null); setExpId(null)
    try {
      const params: any = {}
      if(model === 'random_forest'){
        params.n_estimators = nTrees
        if(maxDepth !== '') params.max_depth = Number(maxDepth)
      }
      const { data } = await api.post('/train', { model_type: model, params })
      setMetrics(data.metrics); setExpId(data.experiment_id)
      localStorage.setItem('last_experiment_id', String(data.experiment_id))
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Train failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="card">
      <h3>Train</h3>
      <p className="helper">Pick a model and run training. The new <code>experiment_id</code> is stored for Estimate.</p>

      <div className="row">
        <label>Model
          <select value={model} onChange={e=>setModel(e.target.value as ModelType)}>
            <option value="linear">Linear</option>
            <option value="random_forest">Random Forest</option>
          </select>
        </label>
        {model === 'random_forest' && (
          <>
            <label>n_estimators
              <input type="number" value={nTrees} min={50} step={50} onChange={e=>setNTrees(Number(e.target.value))}/>
            </label>
            <label>max_depth
              <input type="number" value={maxDepth} min={1} onChange={e=>setMaxDepth(e.target.value === '' ? '' : Number(e.target.value))}/>
            </label>
          </>
        )}
      </div>

      <div style={{marginTop:12, display:'flex', gap:8, flexWrap:'wrap'}}>
        <button className="btn" onClick={onTrain} disabled={loading}>{loading ? 'Training...' : 'Train'}</button>
        {expId && <button className="btn" onClick={() => navigator.clipboard.writeText(String(expId))}>Copy experiment_id</button>}
      </div>

      {error && <div className="alert" style={{marginTop:12}}>{error}</div>}

      {metrics && (
        <div style={{marginTop:12}}>
          <div className="kpi">
            <div className="item"><div title="Mean Squared Error (lower is better)">MSE</div><b>{metrics.mse?.toFixed?.(2) ?? metrics.mse}</b></div>
            <div className="item"><div title="Mean Absolute Error (lower is better)">MAE</div><b>{metrics.mae?.toFixed?.(2) ?? metrics.mae}</b></div>
            <div className="item"><div title="Coefficient of Determination (closer to 1 is better)">R²</div><b>{metrics.r2?.toFixed?.(3) ?? metrics.r2}</b></div>
          </div>
          <h4 style={{marginTop:12}}>Response</h4>
          <pre className="code">{JSON.stringify({experiment_id: expId, metrics}, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
