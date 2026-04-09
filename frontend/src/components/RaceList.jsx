import { useState, useEffect } from 'react'

export default function RaceList({ date, source, onSelectRace }) {
  const [races, setRaces] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [ipBlocked, setIpBlocked] = useState(false)

  useEffect(() => {
    if (!date) return
    setLoading(true)
    setError(null)
    setIpBlocked(false)
    fetch(`/api/races?date=${date}&source=${source}`)
      .then(r => {
        if (r.status === 503) {
          return r.json().then(data => {
            setIpBlocked(true)
            setError(data.message || 'netkeiba.comへの接続がブロックされています')
            setRaces([])
            setLoading(false)
            return null
          })
        }
        return r.json()
      })
      .then(data => {
        if (!data) return
        setRaces(data.races || [])
        if (data.ip_blocked) setIpBlocked(true)
        setLoading(false)
      })
      .catch(err => {
        setError('レース一覧の取得に失敗しました')
        setLoading(false)
      })
  }, [date, source])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-3 border-green-500 border-t-transparent rounded-full mx-auto mb-3"></div>
          <p className="text-gray-400">レース情報を取得中...</p>
        </div>
      </div>
    )
  }

  if (ipBlocked) {
    return (
      <div className="bg-amber-900/30 border border-amber-700 rounded-lg p-4 sm:p-6 space-y-3">
        <div className="flex items-center gap-2 text-amber-300 font-semibold">
          <span className="text-xl">🚫</span>
          <span>netkeiba.com への接続がブロックされています</span>
        </div>
        <p className="text-amber-200/70 text-sm">
          このサーバーのIPアドレスがnetkeiba.comからブロックされているため、レースデータを取得できません。
        </p>
        <div className="bg-amber-950/50 rounded-lg p-3 text-xs text-amber-300/80 space-y-1">
          <p className="font-medium text-amber-300">解決方法:</p>
          <ul className="list-disc list-inside space-y-0.5">
            <li>自宅のPCやサーバーでDocker版を起動する（IPがブロックされていない環境）</li>
            <li>しばらく時間を置いてから再試行する</li>
            <li>HTTP_PROXY環境変数でプロキシを設定する</li>
          </ul>
        </div>
        <button
          onClick={() => {
            fetch('/api/reset_block', { method: 'POST' })
              .then(() => {
                setIpBlocked(false)
                setError(null)
                setLoading(true)
                fetch(`/api/races?date=${date}&source=${source}`)
                  .then(r => r.json())
                  .then(data => {
                    setRaces(data.races || [])
                    setLoading(false)
                  })
                  .catch(() => {
                    setError('再試行に失敗しました')
                    setLoading(false)
                  })
              })
          }}
          className="px-4 py-2 bg-amber-700 text-white rounded-lg text-sm hover:bg-amber-600 transition-colors cursor-pointer"
        >
          🔄 再試行する
        </button>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300">
        ⚠️ {error}
      </div>
    )
  }

  if (races.length === 0) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 text-center text-gray-400">
        <p className="text-4xl mb-3">📭</p>
        <p>この日のレース情報は見つかりませんでした</p>
        <p className="text-sm mt-1">
          {source === 'nar'
            ? '開催がない日の可能性があります'
            : '中央競馬は土日開催です。地方競馬タブなら平日も見れます'}
        </p>
      </div>
    )
  }

  // 開催場ごとにグループ化
  const grouped = {}
  races.forEach(race => {
    const venue = race.venue || '不明'
    if (!grouped[venue]) grouped[venue] = []
    grouped[venue].push(race)
  })

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-300">
        🏁 レース一覧
        <span className="text-sm font-normal text-gray-500 ml-2">
          {Object.keys(grouped).length}場 / {races.length}レース
        </span>
      </h2>
      {Object.entries(grouped).map(([venue, venueRaces]) => (
        <div key={venue} className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
          <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center justify-between">
            <h3 className={`font-bold ${source === 'nar' ? 'text-amber-400' : 'text-green-400'}`}>
              📍 {venue}
            </h3>
            <span className="text-xs text-gray-500">{venueRaces.length}レース</span>
          </div>
          <div className="divide-y divide-gray-800">
            {venueRaces.map(race => (
              <button
                key={race.race_id}
                onClick={() => onSelectRace(race.race_id)}
                className="w-full text-left px-3 sm:px-4 py-2.5 sm:py-3 hover:bg-gray-800/50 transition-colors flex items-center gap-2.5 sm:gap-4 cursor-pointer"
              >
                <span className={`font-bold rounded-lg w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center text-sm sm:text-lg border shrink-0 ${
                  source === 'nar'
                    ? 'bg-amber-900/50 text-amber-400 border-amber-800'
                    : 'bg-green-900/50 text-green-400 border-green-800'
                }`}>
                  {race.race_number}R
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm sm:text-base truncate">
                      {race.race_name || `${race.race_number}R`}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-gray-400 mt-0.5">
                    {race.start_time && <span>🕐 {race.start_time}</span>}
                    {race.course_info && <span>📏 {race.course_info}</span>}
                    {race.horse_count && <span>🐎 {race.horse_count}</span>}
                  </div>
                </div>
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
