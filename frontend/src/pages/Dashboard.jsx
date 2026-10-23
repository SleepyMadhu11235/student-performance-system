import { useCallback, useEffect, useState } from 'react'
import {
  PieChart,
  Pie,
  Cell,
  Legend,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
} from 'recharts'
import StatCard from '../components/common/StatCard'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import { TIER_META } from '../constants/tiers'
import { getDashboard } from '../api/predictions'

const CARD_LINE_COLORS = {
  Excellent: TIER_META.Excellent.color,
  Good: TIER_META.Good.color,
  Pass: TIER_META.Pass.color,
  Fail: TIER_META.Fail.color,
}

function ChartCard({ eyebrow, title, children, height = 280 }) {
  return (
    <div className="bg-paper-card rounded-md shadow-card p-6">
      <p className="label-eyebrow">{eyebrow}</p>
      <h3 className="font-display text-lg text-ink mt-1 mb-4">{title}</h3>
      <div style={{ width: '100%', height }}>{children}</div>
    </div>
  )
}

// Maps the backend's snake_case /api/dashboard payload into the shape this
// page's charts were already built against, adding tier colors along the way.
function normalize(payload) {
  return {
    total: payload.total,
    passRate: payload.pass_rate,
    avgConfidence: payload.avg_confidence,
    pieData: (payload.pie_data ?? []).map((d) => ({ ...d, color: TIER_META[d.name]?.color })),
    barData: payload.bar_data ?? [],
    lineData: payload.line_data ?? [],
  }
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('loading') // 'loading' | 'ready' | 'error'
  const [errorMessage, setErrorMessage] = useState('')

  const load = useCallback(() => {
    setStatus('loading')
    getDashboard()
      .then((payload) => {
        setData(normalize(payload))
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

  if (status === 'loading') return <LoadingState label="Fetching the ledger\u2026" />
  if (status === 'error') return <ErrorState message={errorMessage} onRetry={load} />

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <StatCard
          label="Total Predictions"
          value={data.total}
          sublabel="all-time, on file"
          accent="#B8923F"
        />
        <StatCard
          label="Pass Rate"
          value={data.passRate}
          unit="%"
          sublabel="Pass tier or higher"
          accent={TIER_META.Pass.color}
        />
        <StatCard
          label="Average Confidence"
          value={data.avgConfidence}
          unit="%"
          sublabel="across all predictions"
          accent="#37473C"
        />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ChartCard eyebrow="Distribution" title="Predictions by category">
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={data.pieData}
                dataKey="value"
                nameKey="name"
                innerRadius={64}
                outerRadius={96}
                paddingAngle={2}
                strokeWidth={0}
              >
                {data.pieData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  fontFamily: 'IBM Plex Mono, monospace',
                  fontSize: 12,
                  borderRadius: 4,
                  border: '1px solid #D9DBCE',
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={32}
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard eyebrow="At-Risk Cohort" title="Average feature values &mdash; Fail tier">
          <ResponsiveContainer>
            <BarChart data={data.barData} margin={{ left: -12, right: 8, top: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E3E4D8" vertical={false} />
              <XAxis
                dataKey="feature"
                tick={{ fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 11, fill: '#6B7A6E' }}
                axisLine={{ stroke: '#D9DBCE' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fill: '#6B7A6E' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: '#EEF0E7' }}
                contentStyle={{
                  fontFamily: 'IBM Plex Mono, monospace',
                  fontSize: 12,
                  borderRadius: 4,
                  border: '1px solid #D9DBCE',
                }}
              />
              <Bar dataKey="average" fill={TIER_META.Fail.color} radius={[3, 3, 0, 0]} maxBarSize={42} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      <ChartCard eyebrow="Trend" title="Predictions over time, by category" height={260}>
        <ResponsiveContainer>
          <LineChart data={data.lineData} margin={{ left: -12, right: 8, top: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E3E4D8" vertical={false} />
            <XAxis
              dataKey="week"
              tick={{ fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 11, fill: '#6B7A6E' }}
              axisLine={{ stroke: '#D9DBCE' }}
              tickLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, fill: '#6B7A6E' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                fontFamily: 'IBM Plex Mono, monospace',
                fontSize: 12,
                borderRadius: 4,
                border: '1px solid #D9DBCE',
              }}
            />
            <Legend
              iconType="plainline"
              wrapperStyle={{ fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 12 }}
            />
            {Object.entries(CARD_LINE_COLORS).map(([tier, color]) => (
              <Line
                key={tier}
                type="monotone"
                dataKey={tier}
                stroke={color}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  )
}
