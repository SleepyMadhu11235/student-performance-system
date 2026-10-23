import { useEffect, useState } from 'react'
import { Search, Trash2, Download } from 'lucide-react'
import { TIER_ORDER } from '../constants/tiers'
import GradeBadge from '../components/common/GradeBadge'
import Pagination from '../components/common/Pagination'
import EmptyState from '../components/common/EmptyState'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import { getHistory, deleteHistoryRecord, buildExportCsvUrl } from '../api/predictions'

const PAGE_SIZE = 10
const SEARCH_DEBOUNCE_MS = 350

function formatTimestamp(iso) {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function triggerCsvDownload(url) {
  const link = document.createElement('a')
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export default function History() {
  const [rows, setRows] = useState([])
  const [count, setCount] = useState(0)
  const [status, setStatus] = useState('loading') // 'loading' | 'ready' | 'error'
  const [errorMessage, setErrorMessage] = useState('')

  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [labelFilter, setLabelFilter] = useState('All')
  const [page, setPage] = useState(1)
  const [deletingId, setDeletingId] = useState(null)

  // Debounce the search box so we're not firing a request per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchInput.trim()), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchInput])

  // Any filter change resets back to page 1.
  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, labelFilter])

  useEffect(() => {
    let cancelled = false
    setStatus('loading')

    getHistory({ studentId: debouncedSearch, predictedLabel: labelFilter, page, pageSize: PAGE_SIZE })
      .then((data) => {
        if (cancelled) return
        setRows(data.results)
        setCount(data.count)
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setErrorMessage(err.message)
        setStatus('error')
      })

    return () => {
      cancelled = true
    }
  }, [debouncedSearch, labelFilter, page])

  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE))

  const refetch = () => {
    // Re-triggers the effect above by nudging page to itself via a state copy.
    setStatus('loading')
    getHistory({ studentId: debouncedSearch, predictedLabel: labelFilter, page, pageSize: PAGE_SIZE })
      .then((data) => {
        setRows(data.results)
        setCount(data.count)
        setStatus('ready')
      })
      .catch((err) => {
        setErrorMessage(err.message)
        setStatus('error')
      })
  }

  const handleDelete = async (id) => {
    setDeletingId(id)
    try {
      await deleteHistoryRecord(id)
      // If we just deleted the last row on a page beyond the first, step back a page.
      if (rows.length === 1 && page > 1) {
        setPage((p) => p - 1)
      } else {
        refetch()
      }
    } catch (err) {
      setErrorMessage(err.message)
      setStatus('error')
    } finally {
      setDeletingId(null)
    }
  }

  const handleExport = () => {
    triggerCsvDownload(buildExportCsvUrl({ studentId: debouncedSearch, predictedLabel: labelFilter }))
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by Student ID&hellip;"
              className="pl-9 pr-3 py-2 text-sm bg-paper-card border border-line rounded-md w-64 focus:outline-none focus:border-brass transition-colors"
            />
          </div>
          <select
            value={labelFilter}
            onChange={(e) => setLabelFilter(e.target.value)}
            className="px-3 py-2 text-sm bg-paper-card border border-line rounded-md focus:outline-none focus:border-brass transition-colors"
          >
            <option value="All">All categories</option>
            {TIER_ORDER.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          onClick={handleExport}
          disabled={count === 0}
          className="inline-flex items-center gap-1.5 text-sm border border-line rounded-md px-3.5 py-2 text-ink-soft hover:border-brass hover:text-brass transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Download size={14} /> Export CSV
        </button>
      </div>

      <div className="bg-paper-card rounded-md shadow-card overflow-hidden">
        {status === 'loading' && <LoadingState label="Pulling records\u2026" />}

        {status === 'error' && <ErrorState message={errorMessage} onRetry={refetch} />}

        {status === 'ready' && rows.length === 0 && (
          <EmptyState
            icon={Search}
            title="No matching records"
            description="Try a different Student ID or clear the category filter."
          />
        )}

        {status === 'ready' && rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-line">
                  <th className="label-eyebrow font-normal px-5 py-3">Student</th>
                  <th className="label-eyebrow font-normal px-5 py-3">Input Features</th>
                  <th className="label-eyebrow font-normal px-5 py-3">Label</th>
                  <th className="label-eyebrow font-normal px-5 py-3">Confidence</th>
                  <th className="label-eyebrow font-normal px-5 py-3">Recorded</th>
                  <th className="label-eyebrow font-normal px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr
                    key={r.id}
                    className={`border-b border-line last:border-b-0 ${i % 2 === 1 ? 'bg-paper/50' : ''}`}
                  >
                    <td className="px-5 py-3.5 align-top">
                      <p className="text-ink font-medium">{r.student_id}</p>
                      <p className="text-ink-faint text-xs capitalize">{r.source}</p>
                    </td>
                    <td className="px-5 py-3.5 align-top font-mono text-xs text-ink-faint leading-relaxed">
                      Att {r.attendance_rate} &middot; M1 {r.midterm_1} &middot; M2 {r.midterm_2}
                      <br />
                      Assign {r.assignments_avg} &middot; Study {r.study_hours_weekly}h
                    </td>
                    <td className="px-5 py-3.5 align-top">
                      <div className="flex items-center gap-2">
                        <GradeBadge label={r.predicted_label} size="sm" />
                        <span className="text-ink-soft">{r.predicted_label}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 align-top font-mono text-ink">{r.confidence_score}%</td>
                    <td className="px-5 py-3.5 align-top text-ink-faint text-xs">
                      {formatTimestamp(r.created_at)}
                    </td>
                    <td className="px-5 py-3.5 align-top text-right">
                      <button
                        type="button"
                        onClick={() => handleDelete(r.id)}
                        disabled={deletingId === r.id}
                        className="inline-flex items-center gap-1 text-xs text-ink-faint hover:text-tier-fail transition-colors disabled:opacity-40"
                        aria-label={`Delete record for ${r.student_id}`}
                      >
                        <Trash2 size={13} /> {deletingId === r.id ? 'Deleting\u2026' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {status === 'ready' && rows.length > 0 && (
          <div className="px-5 pb-4">
            <Pagination page={page} totalPages={totalPages} onChange={setPage} />
          </div>
        )}
      </div>
    </div>
  )
}
