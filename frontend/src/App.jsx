import LogsViewer from './components/LogsViewer'

function App() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-6xl">
        <h1 className="text-2xl font-bold mb-6">Contact Report Extraction — Logs</h1>
        <LogsViewer />
      </div>
    </div>
  )
}

export default App
