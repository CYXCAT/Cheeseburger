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
    admin: string
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
    tabAccount: string
    tabUsage: string
    tabBilling: string
    username: string
    newPassword: string
    newPasswordConfirm: string
    updateSuccess: string
    balance: string
    currency: string
    last30dTokens: string
    last30dSpent: string
    usageSummaryTitle: string
    billingLedgerTitle: string
    refresh: string
    tokens: string
    cost: string
    model: string
    day: string
    amount: string
    type: string
    reason: string
    time: string
    recentUsageEventsTitle: string
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
  admin: {
    title: string
    userList: string
    username: string
    createdAt: string
    lastLoginAt: string
    requestCount: string
    totalTokens: string
    balance: string
    topup: string
    topupAmount: string
    topupAmountCents: string
    topupSuccess: string
    never: string
  }
}
