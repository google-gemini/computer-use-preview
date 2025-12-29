package com.example.myllm

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.example.myllm.ui.theme.MyLLMTheme
import com.example.myllm.view.navigation.AppNavigation
import com.example.myllm.service.UserService

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        UserService.initializeUser()

        setContent {
            MyLLMTheme {
                // 내비게이션 Composable만 호출
                AppNavigation()
            }
        }
    }
}