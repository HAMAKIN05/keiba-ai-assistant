import { useState } from 'react'

export default function PromptViewer({ prompt }) {
  const [copied, setCopied] = useState(false)
  const [showFull, setShowFull] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(prompt)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch {
      // fallback
      const textarea = document.createElement('textarea')
      textarea.value = prompt
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    }
  }

  // プロンプトの文字数カウント
  const charCount = prompt ? prompt.length : 0
  const lineCount = prompt ? prompt.split('\n').length : 0

  return (
    <div className="space-y-4">
      {/* 説明 */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-300 mb-2">💡 使い方</h3>
        <ol className="text-sm text-blue-200/70 space-y-1 list-decimal list-inside">
          <li>下のボタンでプロンプトをコピー</li>
          <li><a href="https://www.genspark.ai" target="_blank" rel="noopener" className="underline text-blue-400 hover:text-blue-300">GenSpark</a> を開く</li>
          <li>コピーしたプロンプトをそのまま貼り付けて送信</li>
          <li>AIが過去成績・脚質・展開予想を元に分析＆買い目を提案！</li>
        </ol>
      </div>

      {/* プロンプト情報サマリー */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
        <div className="flex flex-wrap gap-3 text-xs text-gray-400">
          <span>📊 含まれるデータ:</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">レース基本情報</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">全出走馬データ</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">過去5走成績</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">騎手成績</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">脚質分析</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">展開予想材料</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">距離・馬場適性</span>
          <span className="bg-green-900/40 text-green-400 px-2 py-0.5 rounded">通過順・上がり3F</span>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          {charCount.toLocaleString()}文字 / {lineCount}行のプロンプトを生成しました
        </div>
      </div>

      {/* コピーボタン */}
      <button
        onClick={handleCopy}
        className={`w-full py-4 rounded-xl font-bold text-lg transition-all cursor-pointer ${
          copied
            ? 'bg-green-600 text-white shadow-lg shadow-green-600/30'
            : 'bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-500 hover:to-emerald-500 shadow-lg shadow-green-600/20 hover:shadow-green-600/40'
        }`}
      >
        {copied ? '✅ コピーしました！GenSparkに貼り付けてください' : '📋 プロンプトをコピーする（1クリック）'}
      </button>

      {/* GenSparkリンク */}
      <a
        href="https://www.genspark.ai"
        target="_blank"
        rel="noopener noreferrer"
        className="block w-full py-3 rounded-xl font-bold text-center bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-500 hover:to-indigo-500 transition-all shadow-lg shadow-purple-600/20"
      >
        🚀 GenSpark を開く
      </a>

      {/* プロンプトプレビュー */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
          <span className="text-sm font-medium text-gray-400">📝 プロンプトプレビュー</span>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFull(!showFull)}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
            >
              {showFull ? '折り畳む' : '全文表示'}
            </button>
            <button
              onClick={handleCopy}
              className="text-xs text-green-400 hover:text-green-300 transition-colors cursor-pointer"
            >
              コピー
            </button>
          </div>
        </div>
        <pre className={`p-4 text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed overflow-y-auto ${showFull ? 'max-h-[80vh]' : 'max-h-96'}`}>
          {prompt}
        </pre>
      </div>
    </div>
  )
}
