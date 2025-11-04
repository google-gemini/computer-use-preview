package com.example.myllm.screens // ⬅️ [중요] 패키지 선언

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.example.myllm.navigation.AppRoutes // ⬅️ [중요] import 경로
import com.example.myllm.ui.theme.MyLLMTheme

// 시작 화면 Composable
@Composable
fun StartScreen(navController: NavController) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("시작 페이지", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(32.dp))

        Button(
            onClick = { navController.navigate(AppRoutes.CHAT_SCREEN) },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("채팅 페이지로 이동")
        }

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = { navController.navigate(AppRoutes.TEST_SCREEN) },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("테스트 페이지로 이동")
        }
    }
}

// 프리뷰
@Preview(showBackground = true)
@Composable
fun StartScreenPreview() {
    MyLLMTheme {
        StartScreen(navController = rememberNavController())
    }
}