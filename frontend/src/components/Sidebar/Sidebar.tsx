import { Link, useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { useKbChat } from '../../contexts/KbChatContext'
import styles from './Sidebar.module.css'

export interface HistoryItem {
  id: string
  title: string
  kbId: string
}

interface SidebarProps {
  open: boolean
  onToggle: () => void
  /** 历史记录列表（无 context 时可由上层注入） */
  history?: HistoryItem[]
  /** 当前用户展示名 */
  userName?: string
  /** 退出登录回调 */
  onLogout?: () => void
  /** 用户头像 URL */
  userAvatar?: string
  githubUrl?: string
  email?: string
}

const defaultHistory: HistoryItem[] = []

export function Sidebar({
  open,
  onToggle,
  history: historyProp,
  userName = 'User',
  onLogout,
  userAvatar,
  githubUrl = 'https://github.com/CYXCAT/Cheeseburger',
  email = 'mailto:yingxiao649@gmail.com',
}: SidebarProps) {
  const { t } = useI18n()
  const navigate = useNavigate()
  const chatCtx = useKbChat()
  const history: HistoryItem[] = chatCtx
    ? chatCtx.conversations.map((c) => ({
        id: String(c.id),
        title: c.title || t.sidebar.newChat,
        kbId: String(c.kb_id),
      }))
    : (historyProp ?? defaultHistory)

  const handleNewChat = (e: React.MouseEvent) => {
    if (chatCtx) {
      e.preventDefault()
      chatCtx.createNewChat()
      navigate(`/kb/${chatCtx.kbId}`)
    }
  }

  const handleSelect = (item: HistoryItem) => {
    if (chatCtx) {
      chatCtx.selectConversation(Number(item.id))
      navigate(`/kb/${item.kbId}`)
    } else {
      navigate(`/kb/${item.kbId}`)
    }
  }

  const handleDelete = (e: React.MouseEvent, conversationId: number) => {
    e.stopPropagation()
    chatCtx?.deleteConversation(conversationId)
  }

  return (
    <aside
      className={styles.aside}
      data-open={open}
      role="navigation"
      aria-label="Sidebar"
    >
      <button
        type="button"
        className={styles.toggle}
        onClick={onToggle}
        aria-label={open ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        <span className={styles.toggleIcon}>{open ? '‹' : '›'}</span>
      </button>

      <div className={styles.content}>
        <div className={styles.header}>
          <img
            src="/icon1.jpg"
            alt=""
            className={styles.logo}
          />
          <span className={styles.siteName}>Cheeseburger</span>
        </div>

        <Link
          to={chatCtx ? `/kb/${chatCtx.kbId}` : '/'}
          className={styles.newChat}
          onClick={handleNewChat}
        >
          <span className={styles.newChatIcon}>+</span>
          {t.sidebar.newChat}
        </Link>

        <div className={styles.historySection}>
          <span className={styles.historyLabel}>{t.sidebar.history}</span>
          <ul className={styles.historyList}>
            {history.map((item) => (
              <li key={item.id} className={styles.historyRow}>
                <button
                  type="button"
                  className={styles.historyItem}
                  onClick={() => handleSelect(item)}
                >
                  <span className={styles.historyItemTitle}>{item.title}</span>
                </button>
                {chatCtx && (
                  <button
                    type="button"
                    className={styles.historyDelete}
                    onClick={(e) => handleDelete(e, Number(item.id))}
                    title={t.sidebar.deleteItem}
                    aria-label={t.sidebar.deleteItem}
                  >
                    {t.sidebar.deleteItem}
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.footer}>
          <div className={styles.userRow}>
            <div
              className={styles.avatar}
              style={userAvatar ? { backgroundImage: `url(${userAvatar})` } : undefined}
            >
              {!userAvatar && (userName.charAt(0) || '?')}
            </div>
            <span className={styles.userName}>{userName}</span>
          </div>
          <div className={styles.footerLinks}>
            <Link to="/settings" className={styles.footerLink}>{t.sidebar.settings}</Link>
            {onLogout && (
              <button type="button" className={styles.footerLinkBtn} onClick={onLogout}>
                {t.auth.logout}
              </button>
            )}
          </div>
          <div className={styles.links}>
            <a
              href={githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.iconLink}
              aria-label="GitHub"
            >
              <GitHubIcon />
            </a>
            <a
              href={email}
              className={styles.iconLink}
              aria-label="Email"
            >
              <EmailIcon />
            </a>
          </div>
        </div>
      </div>
    </aside>
  )
}

function GitHubIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  )
}

function EmailIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  )
}
