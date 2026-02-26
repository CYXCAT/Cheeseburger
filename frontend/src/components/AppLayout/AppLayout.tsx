import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from '../Sidebar'
import styles from './AppLayout.module.css'

interface AppLayoutProps {
  /** 是否显示侧栏（导航页可不显示或显示简化版） */
  showSidebar?: boolean
}

export function AppLayout({ showSidebar = true }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className={styles.root}>
      {showSidebar && (
        <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen((o) => !o)} />
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
