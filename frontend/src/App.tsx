import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { KbChatProvider } from './contexts/KbChatContext'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute/ProtectedRoute'
import { NavPage } from './pages/NavPage'
import { KbPage } from './pages/KbPage'
import { KbManagePage } from './pages/KbManagePage'
import { LoginPage } from './pages/LoginPage/LoginPage'
import { RegisterPage } from './pages/RegisterPage/RegisterPage'
import { SettingsPage } from './pages/SettingsPage/SettingsPage'
import { AdminPage } from './pages/AdminPage'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<ProtectedRoute><AppLayout showSidebar={false} /></ProtectedRoute>}>
          <Route index element={<NavPage />} />
        </Route>
        <Route path="/kb/:kbId" element={<ProtectedRoute><KbChatProvider><AppLayout showSidebar={true} /></KbChatProvider></ProtectedRoute>}>
          <Route index element={<KbPage />} />
        </Route>
        <Route path="/kb/:kbId/manage" element={<ProtectedRoute><AppLayout showSidebar={false} /></ProtectedRoute>}>
          <Route index element={<KbManagePage />} />
        </Route>
        <Route path="/settings" element={<ProtectedRoute><AppLayout showSidebar={false} /></ProtectedRoute>}>
          <Route index element={<SettingsPage />} />
        </Route>
        <Route path="/admin" element={<ProtectedRoute><AppLayout showSidebar={false} /></ProtectedRoute>}>
          <Route index element={<AdminPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
