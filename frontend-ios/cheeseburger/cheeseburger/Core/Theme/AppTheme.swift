//
//  AppTheme.swift
//  cheeseburger
//
//  与前端 design/tokens.css 保持一致
//

import SwiftUI

enum AppTheme {
    // MARK: - Colors (对应 tokens.css)
    static let bg = Color(hex: "ffffff")
    static let surface = Color(hex: "faf8f5")
    static let surfaceHover = Color(hex: "f5f0e8")
    static let accent = Color(hex: "e8dcc8")
    static let accentStrong = Color(hex: "c9b896")
    static let border = Color(hex: "eae6df")

    static let text = Color(hex: "2c2c2c")
    static let textMuted = Color(hex: "6b6b6b")
    static let textInverse = Color.white

    static let highlight = Color(red: 201/255, green: 184/255, blue: 150/255, opacity: 0.35)
    static let highlightBorder = accentStrong
    static let danger = Color(red: 200/255, green: 60/255, blue: 60/255)

    // MARK: - Layout
    static let radiusSm: CGFloat = 6
    static let radiusMd: CGFloat = 10
    static let radiusLg: CGFloat = 14
}

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
