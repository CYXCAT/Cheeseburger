//
//  cheeseburgerApp.swift
//  cheeseburger
//
//  Created by 程滢晓 on 2026/2/26.
//

import SwiftUI

@main
struct cheeseburgerApp: App {
    @StateObject private var auth = AuthService()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(auth)
        }
    }
}
