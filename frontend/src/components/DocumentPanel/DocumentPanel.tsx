import { useCallback, useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { useI18n } from '../../i18n'
import styles from './DocumentPanel.module.css'

// 使用 jsdelivr 的 legacy worker（MIME 正确），避免 unpkg 返回非 script 类型导致被拒绝执行
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.js`

export type DocType = 'pdf' | 'web' | 'code'

export interface CodeResultDisplay {
  exit_code: number
  result: string
  language?: string
}

export interface DocSource {
  type: DocType
  url?: string
  html?: string
  totalPages?: number
  /** 代码模式：源码 */
  code?: string
  /** 代码模式：执行结果 */
  codeResult?: CodeResultDisplay
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

  if (source.type === 'code') {
    const code = source.code ?? ''
    const res = source.codeResult
    return (
      <div className={styles.wrap}>
        <div className={styles.toolbar}>
          <span className={styles.label}>代码执行</span>
          {res != null && (
            <span className={styles.codeExitCode} data-exit={res.exit_code}>
              exit {res.exit_code}
            </span>
          )}
        </div>
        <div className={styles.scroll}>
          {code && (
            <section className={styles.codeSection}>
              <div className={styles.codeSectionTitle}>代码</div>
              <pre className={styles.codeBlock}>{code}</pre>
            </section>
          )}
          {res != null && (
            <section className={styles.codeSection}>
              <div className={styles.codeSectionTitle}>输出</div>
              <pre className={styles.codeOutput} data-exit={res.exit_code}>
                {res.result || '(无输出)'}
              </pre>
            </section>
          )}
        </div>
      </div>
    )
  }

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
          // 生成式 HTML 预览需运行脚本与表单；与 allow-same-origin 同用时请注意内容来源（仅预览可信/模型输出）
          sandbox="allow-scripts allow-forms allow-same-origin"
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
