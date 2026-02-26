import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { KbChatProvider } from './contexts/KbChatContext'
import { NavPage } from './pages/NavPage'
import { KbPage } from './pages/KbPage'
import { KbManagePage } from './pages/KbManagePage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout showSidebar={false} />}>
        <Route index element={<NavPage />} />
      </Route>
      <Route path="/kb/:kbId" element={<KbChatProvider><AppLayout showSidebar={true} /></KbChatProvider>}>
        <Route index element={<KbPage />} />
      </Route>
      <Route path="/kb/:kbId/manage" element={<AppLayout showSidebar={false} />}>
        <Route index element={<KbManagePage />} />
      </Route>
    </Routes>
  )
}

export default App
