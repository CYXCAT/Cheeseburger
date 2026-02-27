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
    settings: string
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
  auth: {
    login: string
    register: string
    logout: string
    username: string
    password: string
    passwordConfirm?: string
    inviteToken: string
    inviteTokenRequired: string
    loginTitle: string
    registerTitle: string
    noAccount: string
    hasAccount: string
    loginSuccess: string
    registerSuccess: string
    usernameRequired: string
    passwordRequired: string
    passwordMinLength: string
    passwordMismatch: string
  }
  settings: {
    title: string
    username: string
    newPassword: string
    newPasswordConfirm: string
    updateSuccess: string
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
