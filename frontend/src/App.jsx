import { useState } from 'react'
import DateSelector from './components/DateSelector'
import RaceList from './components/RaceList'
import RaceDetail from './components/RaceDetail'

function App() {
  const [source, setSource] = useState('nar') // デフォルトは地方（平日も使えるように）
  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedRaceId, setSelectedRaceId] = useState(null)

  const handleSourceChange = (newSource) => {
    setSource(newSource)
    setSelectedDate(null)
    setSelectedRaceId(null)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-green-900 via-green-800 to-emerald-900 border-b border-green-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl sm:text-3xl">🏇</span>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold text-white tracking-tight">競馬予想 AI アシスタント</h1>
                <p className="text-green-300 text-xs sm:text-sm">データ分析 × GenSpark で的中率UP</p>
              </div>
            </div>
          </div>

          {/* 中央/地方 切り替えタブ */}
          <div className="mt-4 flex gap-1 bg-green-950/50 p-1 rounded-lg border border-green-800/50 max-w-md">
            <button
              onClick={() => handleSourceChange('jra')}
              className={`flex-1 py-2 px-4 rounded-md font-medium text-sm transition-all cursor-pointer ${
                source === 'jra'
                  ? 'bg-green-600 text-white shadow-lg'
                  : 'text-green-300/70 hover:text-white hover:bg-green-800/50'
              }`}
            >
              🏆 中央競馬 (JRA)
            </button>
            <button
              onClick={() => handleSourceChange('nar')}
              className={`flex-1 py-2 px-4 rounded-md font-medium text-sm transition-all cursor-pointer ${
                source === 'nar'
                  ? 'bg-amber-600 text-white shadow-lg'
                  : 'text-green-300/70 hover:text-white hover:bg-green-800/50'
              }`}
            >
              🐴 地方競馬 (NAR)
            </button>
          </div>
        </div>
      </header>

      {/* ソースインジケーター */}
      <div className={`text-center py-1.5 text-xs font-medium ${
        source === 'nar'
          ? 'bg-amber-900/30 text-amber-400 border-b border-amber-800/30'
          : 'bg-green-900/30 text-green-400 border-b border-green-800/30'
      }`}>
        {source === 'nar'
          ? '📍 地方競馬 - 大井・川崎・船橋・浦和・名古屋・園田・高知 ほか（平日も毎日開催）'
          : '📍 中央競馬 (JRA) - 東京・中山・阪神・京都・中京・札幌・函館・小倉・新潟・福島（土日開催）'}
      </div>

      <main className="max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-6">
        {!selectedRaceId ? (
          <div className="space-y-6">
            {/* 日付選択 */}
            <DateSelector
              key={source}
              source={source}
              selectedDate={selectedDate}
              onSelect={(date) => {
                setSelectedDate(date)
                setSelectedRaceId(null)
              }}
            />

            {/* レース一覧 */}
            {selectedDate && (
              <RaceList
                date={selectedDate}
                source={source}
                onSelectRace={(raceId) => setSelectedRaceId(raceId)}
              />
            )}
          </div>
        ) : (
          <div>
            <button
              onClick={() => setSelectedRaceId(null)}
              className="mb-4 flex items-center gap-2 text-green-400 hover:text-green-300 transition-colors cursor-pointer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              レース一覧に戻る
            </button>
            <RaceDetail raceId={selectedRaceId} source={source} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-gray-500 text-sm">
          競馬予想 AI アシスタント - データ分析ツール
        </div>
      </footer>
    </div>
  )
}

export default App
