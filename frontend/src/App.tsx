import { useState } from 'react'
import Header from './components/Header'
import ChatInput from './components/ChatInput'
import PromoBanner from './components/PromoBanner'
import './App.css'

function App() {
  const [showPromo, setShowPromo] = useState(true)

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <h1 className="main-title">¿En qué estás trabajando?</h1>
        <ChatInput />
      </main>
      {showPromo && <PromoBanner onClose={() => setShowPromo(false)} />}
    </div>
  )
}

export default App
