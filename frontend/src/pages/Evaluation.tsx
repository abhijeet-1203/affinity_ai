import { useEffect, useState } from 'react'
import { Button, Card, EmptyState, Skeleton, Stat } from '../components/ui'
import { api } from '../lib/api'
import { useToast } from '../lib/session'

export default function Evaluation() {
  const toast = useToast()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  async function load() {
    setLoading(true)
    try { setData(await api.evaluation()) } catch (error: any) { toast.show(error.message, 'error') } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  async function run() {
    setRunning(true)
    try { const result: any = await api.runEvaluation(5); toast.show(`Evaluation stored: precision@5 ${result.metrics.precision_at_k}.`); await load() }
    catch (error: any) { toast.show(error.message, 'error') } finally { setRunning(false) }
  }

  if (loading) return <div className="stack"><Skeleton height={120} /><Skeleton height={220} /></div>

  const metrics = data?.latest?.metrics

  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Engine evidence</span>
          <h2>Measured offline evaluation</h2>
          <p className="muted small">Synthetic, hand-labelled dataset. These are not real-user outcomes and are not presented as such.</p>
        </div>
        <Button onClick={run} loading={running}>Run evaluation now</Button>
      </div>

      {!metrics ? (
        <EmptyState title="No evaluation has been run in this workspace">{data?.note ?? 'Run it to see measured numbers.'}</EmptyState>
      ) : (
        <>
          <div className="grid grid-4">
            <Stat label="Precision@5" value={metrics.precision_at_k} hint={`random baseline ${metrics.baseline?.precision_at_k}`} />
            <Stat label="Recall@5" value={metrics.recall_at_k} hint="hand-labelled relevance" />
            <Stat label="NDCG@5" value={metrics.ndcg_at_k} hint="graded ranking quality" />
            <Stat label="Coverage" value={`${Math.round(metrics.coverage * 100)}%`} hint={`${metrics.users_evaluated} synthetic members`} />
          </div>

          <div className="grid grid-2" style={{ alignItems: 'start' }}>
            <Card className="stack">
              <h3>Dataset and label definition</h3>
              <p className="small muted">{metrics.dataset_note}</p>
              <p className="small muted">{metrics.label_definition}</p>
              <div className="row-between small"><span className="muted">Pairs considered</span><span>{metrics.pairs_considered}</span></div>
              <div className="row-between small"><span className="muted">Average information coverage</span><span>{Math.round(metrics.avg_information_coverage * 100)}%</span></div>
              <div className="row-between small"><span className="muted">Average available dimensions</span><span>{metrics.avg_available_dimensions} / 4</span></div>
              <div className="row-between small"><span className="muted">Interest diversity</span><span>{Math.round(metrics.interest_diversity * 100)}%</span></div>
              <div className="row-between small"><span className="muted">Score range observed</span><span>{metrics.score_distribution.min}–{metrics.score_distribution.max} (mean {metrics.score_distribution.mean})</span></div>
            </Card>

            <Card className="stack">
              <h3>Semantic similarity sanity check</h3>
              <p className="small muted">{metrics.semantic_check.note}</p>
              <div className="row-between small"><span className="muted">Paraphrase pairs (mean cosine)</span><span>{metrics.semantic_check.paraphrase_mean}</span></div>
              <div className="row-between small"><span className="muted">Unrelated pairs (mean cosine)</span><span>{metrics.semantic_check.unrelated_mean}</span></div>
              <div className="row-between small"><span className="muted">Separation</span><span style={{ fontWeight: 600, color: 'var(--success)' }}>{metrics.semantic_check.separation}</span></div>
              <hr className="divider" />
              <h3 style={{ fontSize: '1rem' }}>What the engine is</h3>
              <ul className="tiny muted" style={{ paddingLeft: '1.1rem' }}>
                {Object.entries(metrics.engine ?? {}).map(([key, value]: any) => <li key={key}><strong>{key}</strong>: {String(value)}</li>)}
              </ul>
              <span className="tiny muted">Stored run: {data.latest.run_id.slice(0, 8)} · {new Date(data.latest.run_at).toLocaleString()} · k={data.latest.k}</span>
            </Card>
          </div>

          {data.runs?.length > 1 ? (
            <Card className="stack">
              <h3>Previous runs</h3>
              <table className="table">
                <thead><tr><th>Run</th><th>When</th><th>k</th><th>Precision@k</th></tr></thead>
                <tbody>
                  {data.runs.map((row: any) => (
                    <tr key={row.run_id}><td>{row.run_id.slice(0, 8)}</td><td>{new Date(row.run_at).toLocaleString()}</td><td>{row.k}</td><td>{row.precision_at_k}</td></tr>
                  ))}
                </tbody>
              </table>
            </Card>
          ) : null}
        </>
      )}
      {toast.node}
    </div>
  )
}
