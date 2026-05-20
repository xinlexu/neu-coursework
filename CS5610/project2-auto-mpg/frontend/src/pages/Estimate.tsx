import { useEffect, useState } from 'react'
import { api } from '../api'

const F = ['cylinders','displacement','horsepower','weight','acceleration','model_year','origin'] as const

const EXAMPLE = { cylinders: 4, displacement: 120, horsepower: 90, weight: 2500, acceleration: 15, model_year: 76, origin: 1 }

export default function Estimate(){
  const [experimentId, setExperimentId] = useState<number | ''>('')
  const [form, setForm] = useState<Record<string, number>>({...EXAMPLE})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    const saved = localStorage.getItem('last_experiment_id')
    if (saved && !experimentId) setExperimentId(Number(saved))
  }, [])

  function setField(k: string, v: string){ const num = v === '' ? NaN : Number(v); setForm(s => ({...s, [k]: num})) }

  async function onPredict(){
    setError(null); setResult(null)
    if (experimentId === '' || Number.isNaN(experimentId)) { setError('experiment_id is required.'); return }
    for (const k of F) { if (Number.isNaN(form[k])) { setError(`"${k}" is required.`); return } }
    setLoading(true)
    try {
      const { data } = await api.post('/predict', { experiment_id: Number(experimentId), input: form })
      setResult(data.output)
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Predict failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="card">
      <h3>Estimate</h3>
      <p className="helper">Use an <code>experiment_id</code> from Train. All fields are numeric.</p>

      <div className="row">
        <label>experiment_id
          <input type="number" value={experimentId} onChange={e=>setExperimentId(e.target.value === '' ? '' : Number(e.target.value))} />
        </label>

        <label>cylinders
          <select value={form.cylinders} onChange={e=>setField('cylinders', e.target.value)}>
            {[3,4,5,6,8].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>

        <label>displacement (ci)
          <input placeholder="e.g., 120" type="number" step="0.1" value={Number.isNaN(form.displacement) ? '' : form.displacement} onChange={e=>setField('displacement', e.target.value)} />
        </label>

        <label>horsepower (hp)
          <input placeholder="e.g., 90" type="number" step="1" value={Number.isNaN(form.horsepower) ? '' : form.horsepower} onChange={e=>setField('horsepower', e.target.value)} />
        </label>

        <label>weight (lb)
          <input placeholder="e.g., 2500" type="number" step="1" value={Number.isNaN(form.weight) ? '' : form.weight} onChange={e=>setField('weight', e.target.value)} />
        </label>

        <label>acceleration (0–60s)
          <input placeholder="e.g., 15" type="number" step="0.1" value={Number.isNaN(form.acceleration) ? '' : form.acceleration} onChange={e=>setField('acceleration', e.target.value)} />
        </label>

        <label>model_year (70–82)
          <input placeholder="e.g., 76" type="number" step="1" value={Number.isNaN(form.model_year) ? '' : form.model_year} onChange={e=>setField('model_year', e.target.value)} />
        </label>

        <label>origin
          <select value={form.origin} onChange={e=>setField('origin', e.target.value)}>
            <option value={1}>1 — US</option>
            <option value={2}>2 — Europe</option>
            <option value={3}>3 — Japan</option>
          </select>
        </label>
      </div>

      <div style={{marginTop:12, display:'flex', gap:8, flexWrap:'wrap'}}>
        <button className="btn" onClick={() => setForm({...EXAMPLE})}>Reset example</button>
        <button className="btn" onClick={onPredict} disabled={loading}>{loading ? 'Predicting...' : 'Predict'}</button>
      </div>

      {error && <div className="alert" style={{marginTop:12}}>{error}</div>}

      {result && (
        <div style={{marginTop:12}}>
          <div className="kpi">
            <div className="item"><div>MPG</div><b>{result.mpg?.toFixed?.(2) ?? result.mpg}</b></div>
            <div className="item"><div>Lower</div><b>{result.interval?.[0]?.toFixed?.(2) ?? result.interval?.[0]}</b></div>
            <div className="item"><div>Upper</div><b>{result.interval?.[1]?.toFixed?.(2) ?? result.interval?.[1]}</b></div>
          </div>
          <h4 style={{marginTop:12}}>Response</h4>
          <pre className="code">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
