package com.example.myllm.view.screens // ⬅️ [중요] 패키지 선언

import android.app.Activity
import android.content.Context
import android.media.projection.MediaProjectionManager
import android.util.Log
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.example.myllm.data.AppChatMessage
import com.example.myllm.repository.ChatRepository
import com.example.myllm.service.ScreenCaptureService
import com.example.myllm.ui.theme.MyLLMTheme
import com.example.myllm.viewmodel.ChatViewModel

class ChatViewModelFactory : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        val repository = ChatRepository()
        return ChatViewModel(repository) as T
    }
}

// 채팅 화면 Composable
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(navController: NavController) {
    // Context를 얻어 Factory에 전달
    val context = LocalContext.current

    // ViewModel 주입 및 Factory 사용
    val chatViewModel: ChatViewModel = viewModel(factory = ChatViewModelFactory())

    // ViewModel 상태를 UI에서 읽기
    val userInput = chatViewModel.userInput
    val messages = chatViewModel.messages
    val isLoading = chatViewModel.isLoading

    val mediaProjectionManager = remember {
        context.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
    }

    // 런처 정의: Activity 결과 처리.
    val screenCaptureLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        // 1. 권한 승인 확인
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            Log.d("ChatScreen", "MediaProjection 권한 승인됨. 서비스 시작 요청.")

            val intent = ScreenCaptureService.getStartIntent(context, result.data, "ChatScreen")
            context.startForegroundService(intent)
        } else {
            Log.e("ChatScreen", "MediaProjection 권한 거부됨.")
            // TODO: 권한 거부 시 로딩 상태 해제 등의 추가 처리 필요 (ViewModel에서 처리할 수도 있음)
        }
        chatViewModel.onCaptureRequestHandled()
    }

    // LaunchedEffect: isCaptureRequested의 변화에 반응
    LaunchedEffect(chatViewModel.isCaptureRequested) {
        if (chatViewModel.isCaptureRequested) {
            Log.d("ChatScreen", "ViewModel 플래그 감지: 스크린샷 권한 요청 시작.")

            // MediaProjectionManager를 통해 권한 요청 Intent 생성
            val intent = mediaProjectionManager.createScreenCaptureIntent()
            // 런처 실행 -> 1번 단계의 콜백으로 결과가 돌아옴
            screenCaptureLauncher.launch(intent)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("LLM 채팅") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "뒤로 가기")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.Bottom
            ) {
                items(messages) { message ->
                    ChatBubble(message)
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TextField(
                    value = userInput,
                    onValueChange = { chatViewModel.updateUserInput(it) },
                    modifier = Modifier
                        .weight(1f)
                        .padding(end = 8.dp),
                    placeholder = { Text("메시지를 입력하세요") },
                    enabled = !isLoading
                )
                Button(
                    onClick = {
                        chatViewModel.processAndSendText(userInput)
                    },
                    enabled = userInput.isNotBlank() && !isLoading,
                    modifier = Modifier.align(Alignment.CenterVertically)
                    ) {
                    Text("전송")
                }
            }
        }
    }
}

// 말풍선 Composable
@Composable
fun ChatBubble(message: AppChatMessage) {
    val alignment = if (message.isUser) Arrangement.End else Arrangement.Start
    val bubbleColor = if (message.isUser) Color(0xFF5DB0FE) else Color(0xFFE0E0E0)
    val textColor = if (message.isUser) Color.White else Color.Black

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = alignment
    ) {
        Box(
            modifier = Modifier
                .background(
                    color = bubbleColor,
                    shape = MaterialTheme.shapes.medium
                )
                .padding(horizontal = 12.dp, vertical = 8.dp)
        ) {
            Text(
                text = message.text,
                color = textColor,
                fontSize = 16.sp,
                textAlign = if (message.isUser) TextAlign.End else TextAlign.Start
            )
        }
    }
}

// 프리뷰
@Preview(showBackground = true)
@Composable
fun ChatScreenPreview() {
    MyLLMTheme {
        ChatScreen(navController = rememberNavController())
    }
}