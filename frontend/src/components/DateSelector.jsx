import { useState, useEffect } from 'react'

export default function DateSelector({ source, selectedDate, onSelect }) {
  const [dates, setDates] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetch(`/api/race_dates?source=${source}`)
      .then(r => r.json())
      .then(data => {
        setDates(data.dates || [])
        setLoading(false)
        if (data.dates?.length > 0 && !selectedDate) {
          // 今日を優先、なければ直近の過去日
          const today = data.dates.find(d => d.is_today)
          if (today) {
            onSelect(today.date)
          } else {
            const pastDates = data.dates.filter(d => d.is_past)
            if (pastDates.length > 0) {
              onSelect(pastDates[pastDates.length - 1].date)
            } else {
              onSelect(data.dates[0].date)
            }
          }
        }
      })
      .catch(() => setLoading(false))
  }, [source])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-400">
        <div className="animate-spin w-5 h-5 border-2 border-green-500 border-t-transparent rounded-full"></div>
        日付を読み込み中...
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-300 mb-3">📅 開催日を選択</h2>
      <div className="flex flex-wrap gap-2">
        {dates.map(d => (
          <button
            key={d.date}
            onClick={() => onSelect(d.date)}
            className={`px-4 py-2 rounded-lg font-medium transition-all cursor-pointer text-sm ${
              selectedDate === d.date
                ? source === 'nar'
                  ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/30'
                  : 'bg-green-600 text-white shadow-lg shadow-green-600/30'
                : d.is_today
                  ? 'bg-gray-800 text-white hover:bg-gray-700 border-2 border-blue-500/50'
                  : d.is_past
                    ? 'bg-gray-800/70 text-gray-400 hover:bg-gray-700 border border-gray-700/50'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
            }`}
          >
            {d.display}
          </button>
        ))}
      </div>
    </div>
  )
}
