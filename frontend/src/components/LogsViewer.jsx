import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

const STATUS_COLORS = {
  pipeline_started: 'bg-blue-100 text-blue-800',
  pipeline_completed: 'bg-green-100 text-green-800',
  scraping: 'bg-yellow-100 text-yellow-800',
  scraping_done: 'bg-green-100 text-green-800',
  scraping_failed: 'bg-red-100 text-red-800',
  login_started: 'bg-blue-100 text-blue-800',
  login_done: 'bg-green-100 text-green-800',
  login_skipped: 'bg-gray-100 text-gray-800',
  retry: 'bg-orange-100 text-orange-800',
  transform_started: 'bg-blue-100 text-blue-800',
  transform_done: 'bg-green-100 text-green-800',
  transform_failed: 'bg-red-100 text-red-800',
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('es-PE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function shortId(uuid) {
  return uuid ? uuid.slice(0, 8) : '—'
}

export default function LogsViewer() {
  const [runs, setRuns] = useState([])
  const today = new Date().toISOString().slice(0, 10)
  const [dateFrom, setDateFrom] = useState(today)
  const [dateTo, setDateTo] = useState(today)
  const [selectedRun, setSelectedRun] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchRuns = async () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    const res = await fetch(`/api/runs?${params}`)
    const data = await res.json()
    setRuns(data)
    setLoading(false)
  }

  const fetchLogs = async (runId) => {
    const res = await fetch(`/api/runs/${runId}/logs`)
    const data = await res.json()
    setLogs(data)
    setSelectedRun(runId)
  }

  useEffect(() => {
    fetchRuns()
  }, [])

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-end gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Desde</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Hasta</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="border rounded px-3 py-2 text-sm"
              />
            </div>
            <Button onClick={fetchRuns} disabled={loading}>
              {loading ? 'Cargando...' : 'Filtrar'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Runs table */}
      <Card>
        <CardHeader>
          <CardTitle>Ejecuciones</CardTitle>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <p className="text-muted-foreground text-sm">No hay ejecuciones en este rango.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run ID</TableHead>
                  <TableHead>Inicio</TableHead>
                  <TableHead>Fin</TableHead>
                  <TableHead>Clientes OK</TableHead>
                  <TableHead>Fallidos</TableHead>
                  <TableHead>Transform</TableHead>
                  <TableHead>Filas</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow
                    key={run.run_id}
                    className={selectedRun === run.run_id ? 'bg-muted' : 'cursor-pointer hover:bg-muted/50'}
                    onClick={() => fetchLogs(run.run_id)}
                  >
                    <TableCell className="font-mono text-xs">
                      {shortId(run.run_id)}
                    </TableCell>
                    <TableCell className="text-sm">{formatDate(run.started_at)}</TableCell>
                    <TableCell className="text-sm">{formatDate(run.finished_at)}</TableCell>
                    <TableCell>
                      <Badge className="bg-green-100 text-green-800">{run.clients_ok}</Badge>
                    </TableCell>
                    <TableCell>
                      {run.clients_failed > 0 ? (
                        <Badge className="bg-red-100 text-red-800">{run.clients_failed}</Badge>
                      ) : (
                        <Badge className="bg-gray-100 text-gray-600">0</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {run.transform_ok ? (
                        <Badge className="bg-green-100 text-green-800">OK</Badge>
                      ) : (
                        <Badge className="bg-red-100 text-red-800">Pendiente</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {run.total_rows ? run.total_rows.toLocaleString() : '—'}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => fetchLogs(run.run_id)}>
                        Ver
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Run detail */}
      {selectedRun && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                Detalle de ejecución <span className="font-mono text-sm">{shortId(selectedRun)}</span>
              </CardTitle>
              <Button variant="outline" size="sm" onClick={() => { setSelectedRun(null); setLogs([]) }}>
                Cerrar
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Hora</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Filas</TableHead>
                  <TableHead>Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-xs">{formatDate(log.created_at)}</TableCell>
                    <TableCell className="text-sm">{log.client || '—'}</TableCell>
                    <TableCell>
                      <Badge className={STATUS_COLORS[log.status] || 'bg-gray-100 text-gray-800'}>
                        {log.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {log.rows_count != null ? log.rows_count.toLocaleString() : '—'}
                    </TableCell>
                    <TableCell className="text-xs text-red-600 max-w-xs truncate">
                      {log.error_message || ''}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
