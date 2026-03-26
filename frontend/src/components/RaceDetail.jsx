import { useState, useEffect } from 'react'
import PromptViewer from './PromptViewer'

export default function RaceDetail({ raceId, source }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('entries')
  const [expandedHorse, setExpandedHorse] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/race/${raceId}/full?source=${source}`)
      .then(r => r.json())
      .then(result => {
        setData(result)
        setLoading(false)
      })
      .catch(err => {
        setError('レース情報の取得に失敗しました')
        setLoading(false)
      })
  }, [raceId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-3 border-green-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-400">レースデータを取得中...</p>
          <p className="text-gray-500 text-xs sm:text-sm mt-1">出走馬・オッズ・過去成績・騎手情報を収集しています</p>
        </div>
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

  if (!data) return null

  const race = data.race
  const prompt = data.prompt

  const bracketColors = {
    '1': 'bg-white text-black',
    '2': 'bg-black text-white border border-gray-600',
    '3': 'bg-red-600 text-white',
    '4': 'bg-blue-600 text-white',
    '5': 'bg-yellow-400 text-black',
    '6': 'bg-green-600 text-white',
    '7': 'bg-orange-500 text-white',
    '8': 'bg-pink-500 text-white',
  }

  const posColor = (pos) => {
    if (pos === '1') return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    if (pos === '2') return 'bg-gray-400/20 text-gray-300 border-gray-400/30'
    if (pos === '3') return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
    if (parseInt(pos) <= 5) return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
    return 'bg-gray-700/50 text-gray-400 border-gray-600/30'
  }

  const hasAnyPast = race.entries.some(e => e.past_races && e.past_races.length > 0)
  const hasAnyJockey = race.entries.some(e => e.jockey_info)
  const pastCount = race.entries.filter(e => e.past_races && e.past_races.length > 0).length
  const jockeyCount = race.entries.filter(e => e.jockey_info).length

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* レースヘッダー */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl border border-gray-700 p-4 sm:p-6">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            {race.race_grade && (
              <span className={`px-2 py-0.5 rounded text-xs font-bold shrink-0 ${
                race.race_grade === 'G1' ? 'bg-yellow-500 text-black' :
                race.race_grade === 'G2' ? 'bg-red-500 text-white' :
                race.race_grade === 'G3' ? 'bg-green-500 text-white' :
                'bg-gray-600 text-white'
              }`}>
                {race.race_grade}
              </span>
            )}
            <h2 className="text-xl sm:text-2xl font-bold text-white">
              {race.race_name || `${race.race_number}R`}
            </h2>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs sm:text-sm text-gray-400 mt-2">
            <span>📍 {race.venue} {race.race_number}R</span>
            {race.date && <span>📅 {race.date}</span>}
            {race.start_time && <span>🕐 {race.start_time}</span>}
            <span>📏 {race.course_type}{race.distance}</span>
            {race.track_condition && <span>🏟️ {race.track_condition}</span>}
            {race.weather && <span>🌤️ {race.weather}</span>}
            <span>🐎 {race.entries.length}頭</span>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5 sm:gap-2">
          <span className="inline-flex items-center gap-1 text-[10px] sm:text-xs bg-gray-800 text-gray-400 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
            {hasAnyPast ? '✅' : '⏳'} 過去成績 {pastCount}/{race.entries.length}
          </span>
          <span className="inline-flex items-center gap-1 text-[10px] sm:text-xs bg-gray-800 text-gray-400 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
            {hasAnyJockey ? '✅' : '⏳'} 騎手 {jockeyCount}/{race.entries.length}
          </span>
          <span className="inline-flex items-center gap-1 text-[10px] sm:text-xs bg-gray-800 text-gray-400 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
            {race.entries.some(e => e.odds) ? '✅' : '⏳'} オッズ
          </span>
        </div>
      </div>

      {/* タブ切り替え */}
      <div className="flex gap-1 bg-gray-900 p-1 rounded-lg border border-gray-800">
        <button
          onClick={() => setActiveTab('entries')}
          className={`flex-1 py-2 px-2 sm:px-4 rounded-md font-medium text-sm transition-all cursor-pointer ${
            activeTab === 'entries'
              ? 'bg-green-700 text-white shadow'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          🐎 出走馬
        </button>
        <button
          onClick={() => setActiveTab('prompt')}
          className={`flex-1 py-2 px-2 sm:px-4 rounded-md font-medium text-sm transition-all cursor-pointer ${
            activeTab === 'prompt'
              ? 'bg-green-700 text-white shadow'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
        >
          🤖 GenSpark
        </button>
      </div>

      {/* タブ内容 */}
      {activeTab === 'entries' && (
        <div className="space-y-3">
          {race.entries.map((entry, idx) => {
            const isExpanded = expandedHorse === idx

            return (
              <div key={idx} className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                {/* 馬の基本情報ヘッダー */}
                <div
                  className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 border-b border-gray-800 cursor-pointer hover:bg-gray-800/30 transition-colors"
                  onClick={() => setExpandedHorse(isExpanded ? null : idx)}
                >
                  <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold shrink-0 ${bracketColors[entry.bracket_number] || 'bg-gray-700 text-white'}`}>
                    {entry.horse_number}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                      <span className="font-bold text-white text-base sm:text-lg">{entry.horse_name}</span>
                      <span className="text-gray-500 text-xs sm:text-sm">{entry.sex_age}</span>
                      {entry.past_races && entry.past_races.length > 0 && (
                        <span className="text-[10px] sm:text-xs bg-blue-900/40 text-blue-400 px-1 sm:px-1.5 py-0.5 rounded">
                          {entry.past_races.length}走
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-x-2 sm:gap-x-3 gap-y-0.5 text-xs sm:text-sm text-gray-400">
                      <span>{entry.jockey_name}</span>
                      <span>{entry.weight}kg</span>
                      <span className="hidden sm:inline">調教師: {entry.trainer}</span>
                      {entry.horse_weight && <span className="hidden sm:inline">{entry.horse_weight}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                    {entry.odds && (
                      <div className="text-right">
                        <div className="text-base sm:text-lg font-bold text-yellow-400">{entry.odds}<span className="text-xs">倍</span></div>
                        <div className="text-[10px] sm:text-xs text-gray-500">{entry.popularity}人気</div>
                      </div>
                    )}
                    <svg
                      className={`w-4 h-4 sm:w-5 sm:h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* 騎手情報 */}
                {entry.jockey_info && (
                  <div className="px-3 sm:px-4 py-2 bg-gray-800/30 border-b border-gray-800">
                    <div className="text-[10px] sm:text-xs text-gray-500 mb-1">👤 {entry.jockey_info.name}</div>
                    <div className="flex flex-wrap gap-x-3 sm:gap-x-4 gap-y-0.5 text-xs sm:text-sm">
                      <span>{entry.jockey_info.rides}<span className="text-gray-500">騎乗</span> <span className="text-green-400">{entry.jockey_info.wins}</span><span className="text-gray-500">勝</span></span>
                      <span>勝率<span className="text-gray-300 font-medium ml-0.5">{entry.jockey_info.win_rate}</span></span>
                      <span>連対<span className="text-gray-300 ml-0.5">{entry.jockey_info.place_rate}</span></span>
                      <span>複勝<span className="text-gray-300 ml-0.5">{entry.jockey_info.show_rate}</span></span>
                    </div>
                  </div>
                )}

                {/* 過去成績 */}
                {entry.past_races && entry.past_races.length > 0 && (
                  <div className={`px-3 sm:px-4 py-2 sm:py-3 ${!isExpanded ? 'max-h-28 sm:max-h-32 overflow-hidden relative' : ''}`}>
                    <div className="text-[10px] sm:text-xs text-gray-500 mb-1.5 sm:mb-2">📊 直近{entry.past_races.length}走</div>

                    {/* モバイル: カード形式 */}
                    <div className="sm:hidden space-y-2">
                      {entry.past_races.map((pr, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs">
                          <span className={`inline-flex items-center justify-center w-7 h-5 rounded text-[10px] font-bold border shrink-0 mt-0.5 ${posColor(pr.position)}`}>
                            {pr.position}着
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1 flex-wrap">
                              <span className="text-gray-500">{pr.date?.slice(5)}</span>
                              <span className="text-gray-300 truncate">{pr.race_name}</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-500 flex-wrap">
                              <span>{pr.course}</span>
                              <span>{pr.track_condition}</span>
                              {pr.time && <span className="text-gray-400 font-mono">{pr.time}</span>}
                              {pr.last_3f && (
                                <span className={`font-mono ${parseFloat(pr.last_3f) < 37 ? 'text-green-400' : 'text-gray-400'}`}>
                                  上{pr.last_3f}
                                </span>
                              )}
                              {pr.passing && <span className="font-mono">{pr.passing}</span>}
                            </div>
                            {isExpanded && (
                              <div className="flex items-center gap-2 text-gray-500 flex-wrap">
                                {pr.horse_weight && <span>{pr.horse_weight}</span>}
                                <span>{pr.jockey}</span>
                                {pr.odds && <span>{pr.odds}倍({pr.popularity}人)</span>}
                                {pr.winner && <span className="truncate">勝:{pr.winner}</span>}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* PC/タブレット: テーブル形式 */}
                    <div className="hidden sm:block overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-xs text-gray-500 border-b border-gray-800">
                            <th className="text-left py-1 pr-2">日付</th>
                            <th className="text-left py-1 pr-2">レース</th>
                            <th className="text-center py-1 pr-2">着順</th>
                            <th className="text-left py-1 pr-2">コース</th>
                            <th className="text-left py-1 pr-2">馬場</th>
                            <th className="text-right py-1 pr-2">タイム</th>
                            <th className="text-left py-1 pr-2">通過</th>
                            <th className="text-right py-1 pr-2">上がり</th>
                            <th className="text-right py-1 pr-2">馬体重</th>
                            {isExpanded && <th className="text-left py-1 pr-2">騎手</th>}
                            {isExpanded && <th className="text-right py-1 pr-2">オッズ</th>}
                            {isExpanded && <th className="text-left py-1">勝ち馬</th>}
                          </tr>
                        </thead>
                        <tbody>
                          {entry.past_races.map((pr, i) => (
                            <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                              <td className="py-1.5 pr-2 text-gray-500 text-xs whitespace-nowrap">{pr.date}</td>
                              <td className="py-1.5 pr-2 text-gray-300 truncate max-w-[120px]" title={pr.race_name}>{pr.race_name}</td>
                              <td className="py-1.5 pr-2 text-center">
                                <span className={`inline-flex items-center justify-center w-8 h-5 rounded text-xs font-bold border ${posColor(pr.position)}`}>
                                  {pr.position}着
                                </span>
                                {pr.field_size && <span className="text-gray-600 text-xs ml-0.5">/{pr.field_size}</span>}
                              </td>
                              <td className="py-1.5 pr-2 text-gray-400 text-xs whitespace-nowrap">{pr.course}</td>
                              <td className="py-1.5 pr-2 text-gray-400 text-xs">{pr.track_condition}</td>
                              <td className="py-1.5 pr-2 text-right text-gray-300 text-xs font-mono">{pr.time}</td>
                              <td className="py-1.5 pr-2 text-gray-400 text-xs font-mono whitespace-nowrap">{pr.passing || '-'}</td>
                              <td className="py-1.5 pr-2 text-right text-xs font-mono">
                                {pr.last_3f ? (
                                  <span className={parseFloat(pr.last_3f) < 37 ? 'text-green-400' : parseFloat(pr.last_3f) < 38 ? 'text-gray-300' : 'text-gray-500'}>
                                    {pr.last_3f}
                                  </span>
                                ) : '-'}
                              </td>
                              <td className="py-1.5 pr-2 text-right text-gray-400 text-xs">{pr.horse_weight || '-'}</td>
                              {isExpanded && <td className="py-1.5 pr-2 text-gray-400 text-xs">{pr.jockey}</td>}
                              {isExpanded && <td className="py-1.5 pr-2 text-right text-gray-400 text-xs">
                                {pr.odds && <>{pr.odds}<span className="text-gray-600">({pr.popularity}人)</span></>}
                              </td>}
                              {isExpanded && <td className="py-1.5 text-gray-500 text-xs truncate max-w-[100px]" title={pr.winner}>{pr.winner}</td>}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* 折り畳み時のグラデーション */}
                    {!isExpanded && (
                      <div className="absolute bottom-0 left-0 right-0 h-8 sm:h-10 bg-gradient-to-t from-gray-900 to-transparent flex items-end justify-center pb-0.5 sm:pb-1">
                        <span className="text-[10px] sm:text-xs text-gray-500">タップで詳細 ▼</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {activeTab === 'prompt' && (
        <PromptViewer prompt={prompt} />
      )}
    </div>
  )
}
