import { useCallback, useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { RefreshCw, Award, CircleAlert } from 'lucide-react'
import { getModels, triggerRetrain } from '../api/predictions'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'

const METRICS = [
  { key: 'accuracy', label: 'Accuracy', color: '#37473C' },
  { key: 'precision', label: 'Precision', color: '#4C6B8A' },
  { key: 'recall', label: 'Recall', color: '#6B8E4E' },
  { key: 'f1', label: 'F1-score', color: '#B8923F' },
]

const asPct = (n) => `${Math.round(n * 100)}%`

function formatTrainedAt(iso) {
  if (!iso) return 'not yet trained'
  const date = new Date(iso)
  const minutesAgo = Math.round((Date.now() - date.getTime()) / 60000)
  if (minutesAgo < 1) return 'trained just now'
  if (minutesAgo < 60) return `trained ${minutesAgo}m ago`
  return `trained ${date.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`
}

export default function Models() {
  const [metrics, setMetrics] = useState(null)
  const [status, setStatus] = useState('loading') // 'loading' | 'ready' | 'error'
  const [errorMessage, setErrorMessage] = useState('')
  const [retraining, setRetraining] = useState(false)
  const [retrainError, setRetrainError] = useState('')

  const load = useCallback(() => {
    setStatus('loading')
    getModels()
      .then((data) => {
        setMetrics(data)
        setStatus('ready')
      })
      .catch((err) => {
        setErrorMessage(err.message)
        setStatus('error')
      })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleRetrain = async () => {
    setRetraining(true)
    setRetrainError('')
    try {
      const fresh = await triggerRetrain()
      setMetrics(fresh)
      setStatus('ready')
    } catch (err) {
      setRetrainError(err.message)
    } finally {
      setRetraining(false)
    }
  }

  if (status === 'loading') return <LoadingState label="Reading the comparison ledger\u2026" />
  if (status === 'error') return <ErrorState message={errorMessage} onRetry={load} />

  const chartData = metrics.models.map((m) => ({
    model: m.model,
    accuracy: m.accuracy,
    precision: m.precision,
    recall: m.recall,
    f1: m.f1,
  }))
  const champion = metrics.models.find((m) => m.is_champion)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="inline-flex items-center gap-2 text-sm text-ink-faint flex-wrap">
          <Award size={16} className="text-brass" />
          Champion model: <span className="text-ink font-medium">{champion?.model}</span>
          <span className="font-mono text-xs">({formatTrainedAt(metrics.trained_at)} &middot; {metrics.dataset_rows} rows)</span>
        </div>
        <button
          type="button"
          onClick={handleRetrain}
          disabled={retraining}
          className="inline-flex items-center gap-2 bg-ink text-paper text-sm px-4 py-2.5 rounded hover:bg-ink-soft transition-colors disabled:opacity-60 disabled:cursor-wait"
        >
          <RefreshCw size={15} className={retraining ? 'animate-spin' : ''} />
          {retraining ? 'Retraining\u2026' : 'Trigger retraining'}
        </button>
      </div>

      {retrainError && (
        <p className="flex items-center gap-1.5 text-sm text-tier-fail">
          <CircleAlert size={14} /> {retrainError}
        </p>
      )}

      <div className="bg-paper-card rounded-md shadow-card p-6">
        <p className="label-eyebrow">Comparison</p>
        <h3 className="font-display text-lg text-ink mt-1 mb-4">
          Accuracy, precision, recall &amp; F1 by algorithm
        </h3>
        <div style={{ width: '100%', height: 340 }}>
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ left: -12, right: 8, top: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E3E4D8" vertical={false} />
              <XAxis
                dataKey="model"
                tick={{ fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 11, fill: '#6B7A6E' }}
                axisLine={{ stroke: '#D9DBCE' }}
                tickLine={false}
              />
              <YAxis
                domain={[0, 1]}
                tickFormatter={asPct}
                tick={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fill: '#6B7A6E' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={(value) => asPct(value)}
                contentStyle={{
                  fontFamily: 'IBM Plex Mono, monospace',
                  fontSize: 12,
                  borderRadius: 4,
                  border: '1px solid #D9DBCE',
                }}
              />
              <Legend wrapperStyle={{ fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 12 }} />
              {METRICS.map((m) => (
                <Bar key={m.key} dataKey={m.key} name={m.label} fill={m.color} radius={[3, 3, 0, 0]} maxBarSize={26} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-paper-card rounded-md shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b border-line">
              <th className="label-eyebrow font-normal px-5 py-3">Algorithm</th>
              {METRICS.map((m) => (
                <th key={m.key} className="label-eyebrow font-normal px-5 py-3">
                  {m.label}
                </th>
              ))}
              <th className="label-eyebrow font-normal px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {metrics.models.map((m, i) => (
              <tr
                key={m.model}
                className={`border-b border-line last:border-b-0 ${i % 2 === 1 ? 'bg-paper/50' : ''}`}
              >
                <td className="px-5 py-3 text-ink font-medium">{m.model}</td>
                <td className="px-5 py-3 font-mono text-ink-soft">{asPct(m.accuracy)}</td>
                <td className="px-5 py-3 font-mono text-ink-soft">{asPct(m.precision)}</td>
                <td className="px-5 py-3 font-mono text-ink-soft">{asPct(m.recall)}</td>
                <td className="px-5 py-3 font-mono text-ink-soft">{asPct(m.f1)}</td>
                <td className="px-5 py-3">
                  {m.is_champion && (
                    <span className="inline-flex items-center gap-1 text-xs font-mono text-brass-deep bg-brass-soft/40 px-2 py-1 rounded">
                      <Award size={11} /> champion
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
