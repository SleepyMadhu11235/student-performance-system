import { useCallback, useRef, useState } from 'react'
import { FileSpreadsheet, UploadCloud, CheckCircle2, RotateCcw, CircleAlert } from 'lucide-react'
import { uploadCsv } from '../../api/predictions'

const STAGES = { IDLE: 'idle', UPLOADING: 'uploading', SUCCESS: 'success', ERROR: 'error' }
const SKIPPED_PREVIEW_LIMIT = 8

export default function BulkUpload() {
  const [stage, setStage] = useState(STAGES.IDLE)
  const [dragActive, setDragActive] = useState(false)
  const [fileName, setFileName] = useState('')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const inputRef = useRef(null)

  const startUpload = useCallback((file) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Only .csv files are accepted.')
      return
    }
    setError('')
    setFileName(file.name)
    setStage(STAGES.UPLOADING)
    setProgress(0)

    uploadCsv(file, (progressEvent) => {
      if (progressEvent.total) {
        setProgress(Math.round((progressEvent.loaded / progressEvent.total) * 100))
      }
    })
      .then((data) => {
        setResult(data)
        setStage(STAGES.SUCCESS)
      })
      .catch((err) => {
        setError(err.message)
        setStage(STAGES.ERROR)
      })
  }, [])

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    startUpload(e.dataTransfer.files?.[0])
  }

  const handleReset = () => {
    setStage(STAGES.IDLE)
    setProgress(0)
    setFileName('')
    setError('')
    setResult(null)
  }

  if (stage === STAGES.SUCCESS && result) {
    const skippedPreview = result.skipped_rows?.slice(0, SKIPPED_PREVIEW_LIMIT) ?? []
    const skippedRemainder = (result.skipped_rows?.length ?? 0) - skippedPreview.length

    return (
      <div className="bg-paper-card rounded-md shadow-card p-10 flex flex-col items-center text-center">
        <div className="w-14 h-14 rounded-full bg-tier-good/10 flex items-center justify-center text-tier-good">
          <CheckCircle2 size={28} />
        </div>
        <h3 className="font-display text-xl text-ink mt-4">Batch processed</h3>
        <p className="text-sm text-ink-faint mt-1">{fileName}</p>

        <div className="grid grid-cols-3 gap-4 mt-7 w-full max-w-md">
          <div className="border border-line rounded-md py-3">
            <p className="font-display text-2xl text-ink">{result.rows_read}</p>
            <p className="text-xs text-ink-faint mt-0.5">rows read</p>
          </div>
          <div className="border border-line rounded-md py-3">
            <p className="font-display text-2xl text-tier-good">{result.predicted}</p>
            <p className="text-xs text-ink-faint mt-0.5">predicted</p>
          </div>
          <div className="border border-line rounded-md py-3">
            <p className="font-display text-2xl text-tier-fail">{result.skipped}</p>
            <p className="text-xs text-ink-faint mt-0.5">skipped</p>
          </div>
        </div>

        {skippedPreview.length > 0 && (
          <div className="mt-6 w-full max-w-md text-left">
            <p className="label-eyebrow">Skipped rows</p>
            <ul className="mt-2 space-y-1.5">
              {skippedPreview.map((row) => (
                <li key={row.row} className="text-xs font-mono text-ink-faint flex gap-2">
                  <span className="text-ink-soft">row {row.row}</span>
                  <span>&mdash;</span>
                  <span>{row.reason}</span>
                </li>
              ))}
            </ul>
            {skippedRemainder > 0 && (
              <p className="text-xs font-mono text-ink-faint mt-1.5">+{skippedRemainder} more</p>
            )}
          </div>
        )}

        <button
          type="button"
          onClick={handleReset}
          className="inline-flex items-center gap-1.5 mt-8 text-sm text-ink-faint hover:text-ink transition-colors"
        >
          <RotateCcw size={14} /> Upload another file
        </button>
      </div>
    )
  }

  if (stage === STAGES.UPLOADING) {
    return (
      <div className="bg-paper-card rounded-md shadow-card p-10 flex flex-col items-center text-center">
        <FileSpreadsheet size={32} className="text-brass" />
        <p className="font-display text-lg text-ink mt-3">{fileName}</p>
        <p className="text-xs text-ink-faint font-mono mt-1">uploading &amp; running batch predictions&hellip;</p>
        <div className="w-full max-w-sm h-2 rounded-full bg-line overflow-hidden mt-5">
          <div
            className="h-full bg-brass transition-all duration-200 ease-out"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
        <p className="font-mono text-xs text-ink-faint mt-2">{Math.min(progress, 100)}%</p>
      </div>
    )
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        className={[
          'bg-paper-card rounded-md p-14 flex flex-col items-center text-center cursor-pointer transition-colors',
          'border-2 border-dashed',
          dragActive ? 'border-brass bg-brass-soft/20' : 'border-line hover:border-brass/60',
        ].join(' ')}
      >
        <UploadCloud size={30} className={dragActive ? 'text-brass' : 'text-ink-faint'} />
        <p className="font-display text-lg text-ink mt-4">
          {dragActive ? 'Drop the roster here' : 'Drag a class roster here'}
        </p>
        <p className="text-sm text-ink-faint mt-1">or click to browse for a .csv file</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => startUpload(e.target.files?.[0])}
        />
      </div>
      {error && (
        <p className="mt-3 flex items-center gap-1.5 text-sm text-tier-fail">
          <CircleAlert size={14} /> {error}
        </p>
      )}
      <p className="mt-4 text-xs text-ink-faint font-mono">
        expected columns: attendance_rate, midterm_1, midterm_2, assignments_avg, study_hours_weekly
        (student_id optional)
      </p>
    </div>
  )
}
