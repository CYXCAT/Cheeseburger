export type Locale = 'zh' | 'en'

export interface I18nDict {
  nav: {
    title: string
    subtitle: string
    selectKb: string
    newChat: string
    createKb: string
    manage: string
  }
  sidebar: {
    history: string
    newChat: string
    user: string
    deleteItem: string
  }
  chat: {
    placeholder: string
    send: string
    thinking: string
    source: string
    jumpToDoc: string
    toolCallsLabel: string
  }
  doc: {
    pdf: string
    webSnapshot: string
    page: string
  }
  common: {
    back: string
    loading: string
    cancel: string
    confirm: string
    save: string
    nameRequired: string
    errorGeneric: string
  }
  manage: {
    title: string
    uploadPdf: string
    uploadUrl: string
    uploadText: string
    preview: string
    confirmUpload: string
    uploaded: string
    deleteDoc: string
    nameLabel: string
    descLabel: string
    urlPlaceholder: string
    textPlaceholder: string
  }
}
