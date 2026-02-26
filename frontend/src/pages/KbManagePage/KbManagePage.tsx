import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { kbApi, docsApi } from '../../api'
import type { KnowledgeBase, DocumentOut } from '../../api'
import styles from './KbManagePage.module.css'

export function KbManagePage() {
  const { kbId } = useParams<{ kbId: string }>()
  const navigate = useNavigate()
  const { t } = useI18n()
  const id = kbId ? parseInt(kbId, 10) : NaN
  const [kb, setKb] = useState<KnowledgeBase | null>(null)
  const [documents, setDocuments] = useState<DocumentOut[]>([])
  const [docsLoading, setDocsLoading] = useState(false)
  const [pineconeRecordCount, setPineconeRecordCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null)
  const [urlInput, setUrlInput] = useState('')
  const [textInput, setTextInput] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDocuments = useCallback(() => {
    if (Number.isNaN(id)) return
    setDocsLoading(true)
    docsApi.listDocuments(id).then(setDocuments).catch(() => setDocuments([])).finally(() => setDocsLoading(false))
  }, [id])

  useEffect(() => {
    if (Number.isNaN(id)) return
    setLoading(true)
    kbApi.get(id).then(setKb).catch(() => setKb(null)).finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!Number.isNaN(id) && kb) {
      loadDocuments()
      docsApi.getPineconeStats(id).then((s) => setPineconeRecordCount(s.record_count)).catch(() => setPineconeRecordCount(null))
    }
  }, [id, kb, loadDocuments])

  useEffect(() => {
    if (!pdfFile) {
      if (pdfPreviewUrl) URL.revokeObjectURL(pdfPreviewUrl)
      setPdfPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(pdfFile)
    setPdfPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [pdfFile])

  const handleUploadPdf = async () => {
    if (!pdfFile || Number.isNaN(id)) return
    setError(null)
    setUploading(true)
    try {
      await docsApi.uploadPdf(id, pdfFile)
      setPdfFile(null)
      loadDocuments()
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
    }
  }

  const handleUploadUrl = async () => {
    const url = urlInput.trim()
    if (!url || Number.isNaN(id)) return
    setError(null)
    setUploading(true)
    try {
      await docsApi.uploadUrl(id, url)
      setUrlInput('')
      loadDocuments()
    } catch (err) {
      setError(err instanceof Error ? err.message : '录入失败')
    } finally {
      setUploading(false)
    }
  }

  const handleUploadText = async () => {
    const text = textInput.trim()
    if (!text || Number.isNaN(id)) return
    setError(null)
    setUploading(true)
    try {
      await docsApi.uploadText(id, text)
      setTextInput('')
      loadDocuments()
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteDoc = async (sourceId: string) => {
    if (Number.isNaN(id)) return
    setError(null)
    try {
      await docsApi.deleteDocument(id, sourceId)
      loadDocuments()
    } catch {
      setError('删除失败')
    }
  }


  if (loading || !kb) {
    return (
      <div className={styles.page}>
        <header className={styles.header}>
          <button type="button" className={styles.back} onClick={() => navigate(-1)}>{t.common.back}</button>
          <span className={styles.title}>{t.common.loading}</span>
        </header>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button type="button" className={styles.back} onClick={() => navigate(`/kb/${id}`)}>
          {t.common.back}
        </button>
        <span className={styles.title}>{t.manage.title} · {kb.name}</span>
      </header>

      <div className={styles.content}>
        {error && <p className={styles.error}>{error}</p>}

        <section className={styles.section} aria-label={t.manage.uploadPdf}>
          <h2 className={styles.sectionTitle}>{t.manage.uploadPdf}</h2>
          <div className={styles.uploadRow}>
            <input
              type="file"
              accept=".pdf,application/pdf"
              className={styles.fileInput}
              onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
            />
            {pdfPreviewUrl && (
              <>
                <span className={styles.previewLabel}>{t.manage.preview}</span>
                <div className={`${styles.previewBox} ${styles.pdfPreviewWrap}`}>
                  <iframe
                    title="PDF preview"
                    src={pdfPreviewUrl}
                    className={styles.pdfIframe}
                  />
                </div>
                <div className={styles.actions}>
                  <button type="button" className={styles.btn} onClick={() => setPdfFile(null)} disabled={uploading}>
                    {t.common.cancel}
                  </button>
                  <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleUploadPdf} disabled={uploading}>
                    {uploading ? t.common.loading : t.manage.confirmUpload}
                  </button>
                </div>
              </>
            )}
          </div>
        </section>

        <section className={styles.section} aria-label={t.manage.uploadUrl}>
          <h2 className={styles.sectionTitle}>{t.manage.uploadUrl}</h2>
          <div className={styles.uploadRow}>
            <input
              type="url"
              className={styles.input}
              placeholder={t.manage.urlPlaceholder}
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
            />
            {urlInput.trim() && (
              <>
                <span className={styles.previewLabel}>{t.manage.preview}</span>
                <div className={styles.previewBox}>
                  <p className={styles.previewText}>将抓取: {urlInput.trim()}</p>
                </div>
                <div className={styles.actions}>
                  <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleUploadUrl} disabled={uploading}>
                    {uploading ? t.common.loading : t.manage.confirmUpload}
                  </button>
                </div>
              </>
            )}
          </div>
        </section>

        <section className={styles.section} aria-label={t.manage.uploadText}>
          <h2 className={styles.sectionTitle}>{t.manage.uploadText}</h2>
          <div className={styles.uploadRow}>
            <textarea
              className={`${styles.input} ${styles.textarea}`}
              placeholder={t.manage.textPlaceholder}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
            />
            {textInput.trim() && (
              <>
                <span className={styles.previewLabel}>{t.manage.preview}</span>
                <div className={styles.previewBox}>
                  <pre className={styles.previewText}>{textInput.trim()}</pre>
                </div>
                <div className={styles.actions}>
                  <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleUploadText} disabled={uploading}>
                    {uploading ? t.common.loading : t.manage.confirmUpload}
                  </button>
                </div>
              </>
            )}
          </div>
        </section>

        <section className={styles.section} aria-label={t.manage.uploaded}>
          <h2 className={styles.sectionTitle}>{t.manage.uploaded}</h2>
          {docsLoading && <p className={styles.muted}>{t.common.loading}</p>}
          {!docsLoading && documents.length === 0 && (
            <p className={styles.muted}>
              {pineconeRecordCount != null && pineconeRecordCount > 0
                ? `Pinecone 中已有 ${pineconeRecordCount} 条向量记录（历史上传未在列表中登记）。新上传的文档将在此列出。`
                : '暂无文档，上传 PDF / 录入网址 / 上传纯文本后将在此列出。'}
            </p>
          )}
          {!docsLoading && documents.length > 0 && (
            <ul className={styles.uploadedList}>
              {documents.map((doc) => (
                <li key={doc.id} className={styles.uploadedItem}>
                  <span>
                    <strong>{doc.source_id}</strong>
                    <span className={styles.uploadedMeta}> · {doc.source_type} · {doc.chunks_count} 段</span>
                  </span>
                  <button
                    type="button"
                    className={`${styles.btn} ${styles.btnDanger}`}
                    onClick={() => handleDeleteDoc(doc.source_id)}
                  >
                    {t.manage.deleteDoc}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
