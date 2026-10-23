import { useState } from 'react'
import { CircleAlert, Loader2, RotateCcw } from 'lucide-react'
import { FEATURE_LIMITS } from '../../constants/features'
import { predictSingle } from '../../api/predictions'
import GradeBadge from '../common/GradeBadge'

const EMPTY_FORM = {
  attendance_rate: '',
  midterm_1: '',
  midterm_2: '',
  assignments_avg: '',
  study_hours_weekly: '',
}

function validate(form) {
  const errors = {}
  Object.entries(FEATURE_LIMITS).forEach(([key, { min, max, label }]) => {
    const raw = form[key]
    if (raw === '' || raw === null) {
      errors[key] = `${label} is required.`
      return
    }
    const value = Number(raw)
    if (Number.isNaN(value)) {
      errors[key] = `${label} must be a number.`
    } else if (value < min || value > max) {
      errors[key] = `${label} must be between ${min} and ${max}.`
    }
  })
  return errors
}

export default function SingleForm() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [touched, setTouched] = useState({})
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const errors = validate(form)
  const hasErrors = Object.keys(errors).length > 0

  const handleChange = (key) => (e) => {
    setForm((f) => ({ ...f, [key]: e.target.value }))
    setResult(null)
  }

  const handleBlur = (key) => () => setTouched((t) => ({ ...t, [key]: true }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setTouched(Object.keys(FEATURE_LIMITS).reduce((acc, k) => ({ ...acc, [k]: true }), {}))
    if (hasErrors) return

    const numericForm = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, Number(v)]))

    setSubmitting(true)
    setSubmitError('')
    try {
      const prediction = await predictSingle(numericForm)
      setResult(prediction)
    } catch (err) {
      setSubmitError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = () => {
    setForm(EMPTY_FORM)
    setTouched({})
    setResult(null)
    setSubmitError('')
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <form onSubmit={handleSubmit} className="lg:col-span-3 bg-paper-card rounded-md shadow-card p-6">
        <p className="label-eyebrow">Student Record</p>
        <h3 className="font-display text-lg text-ink mt-1 mb-5">Enter the five model features</h3>

        <div className="space-y-4">
          {Object.entries(FEATURE_LIMITS).map(([key, { min, max, unit, label, step }]) => (
            <div key={key}>
              <div className="flex items-baseline justify-between">
                <label htmlFor={key} className="text-sm text-ink-soft">
                  {label}
                </label>
                <span className="text-xs font-mono text-ink-faint">
                  {min}&ndash;{max} {unit}
                </span>
              </div>
              <input
                id={key}
                type="number"
                inputMode="decimal"
                step={step}
                min={min}
                max={max}
                value={form[key]}
                onChange={handleChange(key)}
                onBlur={handleBlur(key)}
                placeholder={`e.g. ${key === 'study_hours_weekly' ? '12' : '78'}`}
                className="ledger-input"
                aria-invalid={Boolean(touched[key] && errors[key])}
                aria-describedby={`${key}-error`}
              />
              {touched[key] && errors[key] && (
                <p id={`${key}-error`} className="mt-1 flex items-center gap-1 text-xs text-tier-fail">
                  <CircleAlert size={12} /> {errors[key]}
                </p>
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 mt-6">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 bg-ink text-paper text-sm px-5 py-2.5 rounded hover:bg-ink-soft transition-colors disabled:opacity-60 disabled:cursor-wait"
          >
            {submitting && <Loader2 size={14} className="animate-spin" />}
            {submitting ? 'Predicting\u2026' : 'Run prediction'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-1.5 text-sm text-ink-faint hover:text-ink transition-colors"
          >
            <RotateCcw size={14} /> Clear form
          </button>
        </div>

        {submitError && (
          <p className="mt-4 flex items-center gap-1.5 text-sm text-tier-fail">
            <CircleAlert size={14} /> {submitError}
          </p>
        )}
      </form>

      <div className="lg:col-span-2">
        {result ? (
          <div className="bg-paper-card rounded-md shadow-card p-6 h-full">
            <p className="label-eyebrow">Result &middot; {result.student_id}</p>
            <div className="flex items-center gap-4 mt-3">
              <GradeBadge label={result.predicted_label} size="lg" />
              <div>
                <p className="font-display text-2xl text-ink">{result.predicted_label}</p>
                <p className="text-sm text-ink-faint font-mono">recorded to the ledger</p>
              </div>
            </div>

            <div className="mt-6">
              <p className="label-eyebrow">Confidence</p>
              <div className="mt-2 flex items-center gap-3">
                <div className="flex-1 h-2 rounded-full bg-line overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${result.confidence_score}%`, backgroundColor: '#B8923F' }}
                  />
                </div>
                <span className="font-mono text-sm text-ink w-12 text-right">{result.confidence_score}%</span>
              </div>
            </div>

            <div className="mt-6 pt-5 border-t border-line">
              <p className="label-eyebrow">Explanation</p>
              <p className="mt-2 text-sm text-ink-soft leading-relaxed">{result.rule_based_explanation}</p>
            </div>
          </div>
        ) : (
          <div className="bg-paper-card rounded-md shadow-card p-6 h-full flex flex-col items-center justify-center text-center">
            <span
              className="inline-flex items-center justify-center rounded-stamp font-display text-3xl text-ink-faint/60 select-none"
              style={{ width: 84, height: 84, border: '3px dashed #D9DBCE', transform: 'rotate(-6deg)' }}
            >
              ?
            </span>
            <p className="font-display text-lg text-ink mt-4">No prediction yet</p>
            <p className="text-sm text-ink-faint mt-1 max-w-[220px]">
              Fill in the record and run a prediction to see the result stamped here.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
