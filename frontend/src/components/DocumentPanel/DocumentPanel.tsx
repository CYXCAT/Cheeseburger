import { useCallback, useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { useI18n } from '../../i18n'
import styles from './DocumentPanel.module.css'

// 使用 jsdelivr 的 legacy worker（MIME 正确），避免 unpkg 返回非 script 类型导致被拒绝执行
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.js`

export type DocType = 'pdf' | 'web'

export interface DocSource {
  type: DocType
  /** PDF 的 URL 或网页快照的 URL / HTML 片段标识 */
  url?: string
  /** 网页快照的 HTML（用于 iframe srcdoc 或直接渲染） */
  html?: string
  /** 总页数（PDF）或锚点列表（web） */
  totalPages?: number
}

export interface HighlightRegion {
  pageNumber?: number
  selector?: string
  text?: string
}

interface DocumentPanelProps {
  source: DocSource
  /** 当前高亮区域，用于定位与高亮显示 */
  highlight?: HighlightRegion | null
  /** 点击文档内某处时回调（用于跳转定位，如点击引用） */
  onNavigate?: (region: HighlightRegion) => void
  /** 可选：外部控制的当前页码（PDF） */
  currentPage?: number
  onPageChange?: (page: number) => void
}

export function DocumentPanel({
  source,
  highlight,
  onNavigate: _onNavigate,
  currentPage = 1,
  onPageChange,
}: DocumentPanelProps) {
  const { t } = useI18n()
  const [numPages, setNumPages] = useState<number | null>(source.totalPages ?? null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)

  const onPdfLoad = useCallback(
    ({ numPages: n }: { numPages: number }) => {
      setNumPages(n)
      setLoading(false)
    },
    []
  )

  useEffect(() => {
    if (highlight?.pageNumber) {
      const el = document.getElementById(`doc-page-${highlight.pageNumber}`)
      el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [highlight?.pageNumber])

  if (source.type === 'pdf') {
    const hasPdfUrl = Boolean(source.url)
    return (
      <div className={styles.wrap}>
        <div className={styles.toolbar}>
          <span className={styles.label}>{t.doc.pdf}</span>
          {numPages != null && (
            <span className={styles.pages}>
              {t.doc.page} {currentPage} / {numPages}
            </span>
          )}
        </div>
        <div className={styles.scroll}>
          {!hasPdfUrl && (
            <div className={styles.loading}>
              请配置 PDF 地址（source.url）或使用网页快照
            </div>
          )}
          {hasPdfUrl && loading && (
            <div className={styles.loading}>{t.common.loading}</div>
          )}
          {hasPdfUrl && loadError && (
            <div className={styles.loading}>PDF 加载失败，请检查地址或使用示例网页快照。</div>
          )}
          {hasPdfUrl && !loadError && (
            <Document
              file={source.url}
              onLoadSuccess={onPdfLoad}
              onLoadError={() => { setLoading(false); setLoadError(true) }}
              loading=""
            >
              {numPages != null &&
                Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => (
                  <div
                    key={pageNum}
                    id={`doc-page-${pageNum}`}
                    className={styles.pageWrap}
                    data-highlight={highlight?.pageNumber === pageNum}
                  >
                    <Page
                      pageNumber={pageNum}
                      renderTextLayer
                      renderAnnotationLayer
                      onClick={() => onPageChange?.(pageNum)}
                    />
                  </div>
                ))}
            </Document>
          )}
        </div>
      </div>
    )
  }

  // 网页快照
  return (
    <div className={styles.wrap}>
      <div className={styles.toolbar}>
        <span className={styles.label}>{t.doc.webSnapshot}</span>
      </div>
      <div className={styles.scroll}>
        <iframe
          title="Web snapshot"
          className={styles.iframe}
          srcDoc={source.html || undefined}
          src={source.url && !source.html ? source.url : undefined}
          sandbox="allow-same-origin"
        />
        {highlight?.selector && (
          <div
            className={styles.highlightOverlay}
            data-selector={highlight.selector}
            aria-hidden
          />
        )}
      </div>
    </div>
  )
}
