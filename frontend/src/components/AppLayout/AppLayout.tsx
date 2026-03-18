import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { Sidebar } from '../Sidebar'
import { useAuth } from '../../contexts/AuthContext'
import styles from './AppLayout.module.css'

interface AppLayoutProps {
  /** 是否显示侧栏（导航页可不显示或显示简化版） */
  showSidebar?: boolean
}

export function AppLayout({ showSidebar = true }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className={styles.root}>
      {showSidebar && (
        <Sidebar
          open={sidebarOpen}
          onToggle={() => setSidebarOpen((o) => !o)}
          userName={user?.username ?? 'User'}
          isAdmin={user?.is_admin ?? false}
          onLogout={handleLogout}
        />
      )}
      <main
        className={styles.main}
        data-sidebar-open={showSidebar ? sidebarOpen : undefined}
      >
        <Outlet />
      </main>
    </div>
  )
}
