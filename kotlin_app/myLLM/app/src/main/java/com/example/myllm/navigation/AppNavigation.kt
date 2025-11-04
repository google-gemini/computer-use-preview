package com.example.myllm.navigation // ⬅️ [중요] 패키지 선언

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.myllm.screens.ChatScreen     // ⬅️ [중요] import 경로
import com.example.myllm.screens.StartScreen  // ⬅️ [중요] import 경로
import com.example.myllm.screens.TestScreen   // ⬅️ [중요] import 경로

// 화면 경로(Route)를 정의하는 객체
object AppRoutes {
    const val START_SCREEN = "start"
    const val CHAT_SCREEN = "chat"
    const val TEST_SCREEN = "test"
}

// Jetpack Navigation 설정
@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = AppRoutes.START_SCREEN) {
        // 1. 시작 화면
        composable(AppRoutes.START_SCREEN) {
            StartScreen(navController = navController)
        }

        // 2. 채팅 화면
        composable(AppRoutes.CHAT_SCREEN) {
            ChatScreen(navController = navController)
        }

        // 3. 테스트 화면
        composable(AppRoutes.TEST_SCREEN) {
            TestScreen(navController = navController)
        }
    }
}