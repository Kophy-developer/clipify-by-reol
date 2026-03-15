import { useState, useCallback, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const API = axios.create({ baseURL: API_BASE, timeout: 30000 })

const STAGES = {
  pending: 'Queued',
  ingesting: 'Downloading video',
  transcribing: 'Transcribing',
  detecting_clips: 'Finding best clip',
  rendering: 'Rendering clip',
  burning_subtitles: 'Adding subtitles',
  publishing: 'Publishing',
  scheduled: 'Scheduled',
  completed: 'Done',
  failed: 'Failed',
}

export default function App() {
  const [mode, setMode] = useState('url') // 'url' | 'file'
  const [url, setUrl] = useState('')
  const [file, setFile] = useState(null)
  const [scheduledAt, setScheduledAt] = useState('') // optional ISO or datetime-local
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const poll = useCallback(async (id) => {
    const { data } = await API.get(`/status/${id}`)
    setStatus(data)
    if (data.stage === 'completed' || data.stage === 'failed') {
      const res = await API.get(`/results/${id}`)
      setResults(res.data)
      return true
    }
    return false
  }, [])

  useEffect(() => {
    if (!jobId || (status && (status.stage === 'completed' || status.stage === 'failed'))) return
    const interval = setInterval(async () => {
      const done = await poll(jobId)
      if (done) clearInterval(interval)
    }, 2000)
    return () => clearInterval(interval)
  }, [jobId, status?.stage, poll])

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setResults(null)
    setLoading(true)
    try {
      let res
      const form = new FormData()
      if (mode === 'url') {
        if (!url.trim()) {
          setError('Enter a video URL')
          setLoading(false)
          return
        }
        form.append('url', url.trim())
      } else {
        if (!file) {
          setError('Choose a video file')
          setLoading(false)
          return
        }
        form.append('file', file)
      }
      if (scheduledAt.trim()) {
        // datetime-local is YYYY-MM-DDTHH:mm; backend expects ISO
        const iso = scheduledAt.includes('T') ? new Date(scheduledAt).toISOString() : `${scheduledAt}T00:00:00Z`
        form.append('scheduled_at', iso)
      }
      res = await API.post('/ingest', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setJobId(res.data.job_id)
      setStatus({ stage: 'pending', message: 'Queued' })
      await poll(res.data.job_id)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <header className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Clipify by Reol
          </h1>
          <p className="text-slate-400 mt-2">
            45–60s vertical clips with subtitles → TikTok, Reels, Shorts
          </p>
        </header>

        <form onSubmit={submit} className="space-y-4">
          <div className="flex gap-2 border-b border-slate-700 pb-4">
            <button
              type="button"
              onClick={() => setMode('url')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                mode === 'url'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Video URL
            </button>
            <button
              type="button"
              onClick={() => setMode('file')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                mode === 'file'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Upload file
            </button>
          </div>

          {mode === 'url' && (
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste video URL (YouTube, etc.)"
              className="w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-600 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50"
            />
          )}
          {mode === 'file' && (
            <label className="block">
              <span className="sr-only">Choose video file</span>
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-amber-500/20 file:text-amber-400 file:font-medium hover:file:bg-amber-500/30"
              />
            </label>
          )}

          <label className="block">
            <span className="text-slate-400 text-sm">Publish later (optional)</span>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="mt-1 w-full px-4 py-2 rounded-xl bg-slate-800/80 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            />
          </label>

          {error && (
            <p className="text-red-400 text-sm">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-amber-500 text-slate-950 font-semibold hover:bg-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? 'Processing…' : 'Generate clip'}
          </button>
        </form>

        {status && (
          <section className="mt-8 p-4 rounded-xl bg-slate-800/50 border border-slate-700">
            <h2 className="font-semibold text-slate-200 mb-2">Status</h2>
            <p className="text-amber-400">
              {STAGES[status.stage] || status.stage}: {status.message || '—'}
            </p>
            {status.error && (
              <p className="text-red-400 text-sm mt-2">{status.error}</p>
            )}
            {jobId && (
              <p className="text-slate-500 text-xs mt-2 font-mono">{jobId}</p>
            )}
          </section>
        )}

        {results && (
          <section className="mt-6 p-4 rounded-xl bg-slate-800/50 border border-slate-700">
            <h2 className="font-semibold text-slate-200 mb-3">Results</h2>
            {results.stage === 'failed' && results.error && (
              <p className="text-red-400 text-sm mb-3">{results.error}</p>
            )}
            {results.clip_url && (
              <div className="mb-4">
                <p className="text-slate-400 text-sm mb-2">Preview</p>
                <video
                  src={API_BASE ? `${API_BASE}${results.clip_url}` : results.clip_url}
                  controls
                  className="w-full max-h-[70vh] rounded-lg bg-black"
                  playsInline
                />
                <a
                  href={API_BASE ? `${API_BASE}${results.clip_url}` : results.clip_url}
                  download={`clipify-${jobId || 'clip'}.mp4`}
                  className="inline-block mt-2 text-sm px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/40 hover:bg-amber-500/30"
                >
                  Download clip
                </a>
              </div>
            )}
            <ul className="space-y-2">
              {results.results?.map((r) => (
                <li key={r.platform} className="flex items-center justify-between gap-2">
                  <span className="capitalize text-slate-300">{r.platform}</span>
                  <span className={r.status === 'published' ? 'text-emerald-400' : 'text-red-400'}>
                    {r.status}
                  </span>
                  {r.url && (
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-amber-400 hover:underline truncate max-w-[180px]"
                    >
                      {r.url}
                    </a>
                  )}
                </li>
              ))}
            </ul>
            {results.clips?.length > 0 && (
              <p className="text-slate-500 text-sm mt-3">
                Clip: {results.clips[0].start_time}s – {results.clips[0].end_time}s
                {results.clips[0].confidence != null && ` (confidence ${results.clips[0].confidence})`}
              </p>
            )}
            {results.clips?.[0]?.clip_id && results.results?.some((r) => r.status !== 'published') && (
              <button
                type="button"
                onClick={async () => {
                  try {
                    await API.post(`/retry/${results.clips[0].clip_id}`)
                    setStatus((s) => s ? { ...s, stage: 'publishing', message: 'Retrying…' } : null)
                    const interval = setInterval(async () => {
                      if (!jobId) return
                      const { data } = await API.get(`/status/${jobId}`)
                      setStatus(data)
                      if (data.stage === 'completed' || data.stage === 'failed') {
                        clearInterval(interval)
                        const res = await API.get(`/results/${jobId}`)
                        setResults(res.data)
                      }
                    }, 2000)
                  } catch (e) {
                    setError(e.response?.data?.detail || e.message)
                  }
                }}
                className="mt-3 text-sm px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/40 hover:bg-amber-500/30"
              >
                Retry failed uploads
              </button>
            )}
          </section>
        )}
      </div>
    </div>
  )
}
