import type { I18nDict } from './types'

export const en: I18nDict = {
  nav: {
    title: 'Cheeseburger',
    subtitle: 'Select a knowledge base to start',
    selectKb: 'Select knowledge base',
    newChat: 'New chat',
    createKb: 'Create knowledge base',
    manage: 'Manage',
  },
  sidebar: {
    history: 'History',
    newChat: 'New chat',
    user: 'User',
    deleteItem: 'Delete',
  },
  chat: {
    placeholder: 'Ask a question…',
    send: 'Send',
    thinking: 'Thinking…',
    source: 'Source',
    jumpToDoc: 'Jump to document',
    toolCallsLabel: 'Tools used',
  },
  doc: {
    pdf: 'PDF preview',
    webSnapshot: 'Web snapshot',
    page: 'Page',
  },
  common: {
    back: 'Back',
    loading: 'Loading…',
    cancel: 'Cancel',
    confirm: 'Confirm',
    save: 'Save',
    nameRequired: 'Name is required',
    errorGeneric: 'Operation failed',
  },
  manage: {
    title: 'Manage knowledge base',
    uploadPdf: 'Upload PDF',
    uploadUrl: 'Add URL',
    uploadText: 'Upload text',
    preview: 'Preview',
    confirmUpload: 'Confirm upload',
    uploaded: 'Uploaded',
    deleteDoc: 'Delete',
    nameLabel: 'Name',
    descLabel: 'Description',
    urlPlaceholder: 'https://example.com/page',
    textPlaceholder: 'Enter plain text to add to the knowledge base…',
  },
}
