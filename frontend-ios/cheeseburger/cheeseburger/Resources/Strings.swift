//
//  Strings.swift
//  cheeseburger
//
//  与 frontend i18n 一致，当前仅中文
//

import Foundation

enum L10n {
    static var isZh: Bool { Locale.current.language.languageCode?.identifier == "zh" }

    enum Nav {
        static var title: String { L10n.isZh ? "Cheeseburger" : "Cheeseburger" }
        static var subtitle: String { L10n.isZh ? "选择知识库开始问询" : "Select a knowledge base to start" }
        static var selectKb: String { L10n.isZh ? "选择知识库" : "Select knowledge base" }
        static var newChat: String { L10n.isZh ? "新对话" : "New chat" }
        static var createKb: String { L10n.isZh ? "创建知识库" : "Create knowledge base" }
        static var manage: String { L10n.isZh ? "管理" : "Manage" }
    }

    enum Sidebar {
        static var history: String { L10n.isZh ? "历史记录" : "History" }
        static var newChat: String { L10n.isZh ? "新对话" : "New chat" }
        static var settings: String { L10n.isZh ? "设置" : "Settings" }
        static var deleteItem: String { L10n.isZh ? "删除" : "Delete" }
    }

    enum Chat {
        static var placeholder: String { L10n.isZh ? "输入您的问题…" : "Ask a question…" }
        static var send: String { L10n.isZh ? "发送" : "Send" }
        static var thinking: String { L10n.isZh ? "思考中…" : "Thinking…" }
        static var source: String { L10n.isZh ? "引用来源" : "Source" }
        static var toolCallsLabel: String { L10n.isZh ? "已调用工具" : "Tools used" }
    }

    enum Common {
        static var back: String { L10n.isZh ? "返回" : "Back" }
        static var loading: String { L10n.isZh ? "加载中…" : "Loading…" }
        static var cancel: String { L10n.isZh ? "取消" : "Cancel" }
        static var save: String { L10n.isZh ? "保存" : "Save" }
        static var nameRequired: String { L10n.isZh ? "请输入名称" : "Name is required" }
        static var errorGeneric: String { L10n.isZh ? "操作失败" : "Operation failed" }
    }

    enum Auth {
        static var login: String { L10n.isZh ? "登录" : "Login" }
        static var register: String { L10n.isZh ? "注册" : "Register" }
        static var logout: String { L10n.isZh ? "退出" : "Log out" }
        static var username: String { L10n.isZh ? "用户名" : "Username" }
        static var password: String { L10n.isZh ? "密码" : "Password" }
        static var passwordConfirm: String { L10n.isZh ? "确认密码" : "Confirm password" }
        static var inviteToken: String { L10n.isZh ? "邀请码" : "Invite code" }
        static var inviteTokenRequired: String { L10n.isZh ? "请填写邀请码（从邀请链接获取）" : "Invite code is required (get it from your invite link)" }
        static var loginTitle: String { L10n.isZh ? "登录" : "Login" }
        static var registerTitle: String { L10n.isZh ? "注册" : "Register" }
        static var noAccount: String { L10n.isZh ? "还没有账号？去注册" : "Don't have an account? Register" }
        static var hasAccount: String { L10n.isZh ? "已有账号？去登录" : "Already have an account? Login" }
        static var usernameRequired: String { L10n.isZh ? "请输入用户名" : "Username is required" }
        static var passwordRequired: String { L10n.isZh ? "请输入密码" : "Password is required" }
        static var passwordMinLength: String { L10n.isZh ? "密码至少 6 位" : "Password must be at least 6 characters" }
        static var passwordMismatch: String { L10n.isZh ? "两次密码不一致" : "Passwords do not match" }
    }

    enum Settings {
        static var title: String { L10n.isZh ? "账号设置" : "Account settings" }
        static var username: String { L10n.isZh ? "用户名" : "Username" }
        static var newPassword: String { L10n.isZh ? "新密码" : "New password" }
        static var newPasswordConfirm: String { L10n.isZh ? "确认新密码" : "Confirm new password" }
        static var updateSuccess: String { L10n.isZh ? "保存成功" : "Saved successfully" }
    }

    enum Manage {
        static var title: String { L10n.isZh ? "知识库管理" : "Manage knowledge base" }
        static var uploadPdf: String { L10n.isZh ? "上传 PDF" : "Upload PDF" }
        static var uploadUrl: String { L10n.isZh ? "录入网址" : "Add URL" }
        static var uploadText: String { L10n.isZh ? "上传纯文本" : "Upload text" }
        static var preview: String { L10n.isZh ? "预览" : "Preview" }
        static var confirmUpload: String { L10n.isZh ? "确认上传" : "Confirm upload" }
        static var uploaded: String { L10n.isZh ? "已上传" : "Uploaded" }
        static var deleteDoc: String { L10n.isZh ? "删除" : "Delete" }
        static var nameLabel: String { L10n.isZh ? "名称" : "Name" }
        static var descLabel: String { L10n.isZh ? "描述" : "Description" }
        static var urlPlaceholder: String { L10n.isZh ? "https://example.com/page" : "https://example.com/page" }
        static var textPlaceholder: String { L10n.isZh ? "输入要存入知识库的纯文本…" : "Enter plain text to add to the knowledge base…" }
        static var searchPlaceholder: String { L10n.isZh ? "检索知识库…" : "Search knowledge base…" }
        static var searchButton: String { L10n.isZh ? "检索" : "Search" }
    }
}
