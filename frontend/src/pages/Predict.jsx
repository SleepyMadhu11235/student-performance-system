import { useState } from 'react'
import SingleForm from '../components/predict/SingleForm'
import BulkUpload from '../components/predict/BulkUpload'

const TABS = [
  { key: 'single', label: 'Single Prediction' },
  { key: 'bulk', label: 'Bulk Upload' },
]

export default function Predict() {
  const [tab, setTab] = useState('single')

  return (
    <div className="space-y-6">
      <div className="inline-flex bg-paper-card rounded-md shadow-card p-1">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={[
              'px-4 py-2 text-sm rounded transition-colors font-body',
              tab === key ? 'bg-ink text-paper' : 'text-ink-faint hover:text-ink',
            ].join(' ')}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'single' ? <SingleForm /> : <BulkUpload />}
    </div>
  )
}
