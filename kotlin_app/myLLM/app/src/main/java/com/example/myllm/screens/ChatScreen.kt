package com.example.myllm.screens // ⬅️ [중요] 패키지 선언

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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.aallam.openai.api.chat.ChatCompletionRequest
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.api.model.ModelId
import com.aallam.openai.client.OpenAI
import com.example.myllm.BuildConfig
import com.example.myllm.data.AppChatMessage // ⬅️ [중요] import 경로
import com.example.myllm.ui.theme.MyLLMTheme
import kotlinx.coroutines.launch

// 채팅 화면 Composable
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(navController: NavController) {
    var userInput by remember { mutableStateOf("") }
    var messages by remember { mutableStateOf(listOf<AppChatMessage>()) }
    var isLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    val openai = remember {
        OpenAI(BuildConfig.OPENAI_API_KEY)
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
                    onValueChange = { userInput = it },
                    modifier = Modifier
                        .weight(1f)
                        .padding(end = 8.dp),
                    placeholder = { Text("메시지를 입력하세요")},
                    enabled = !isLoading
                )

                Button(
                    onClick = {
                        if (userInput.isNotBlank() && !isLoading) {

                            val userMessage = AppChatMessage(userInput, true)
                            val currentInput = userInput
                            messages = messages + userMessage

                            val chatHistory = messages.map {
                                ChatMessage(
                                    role = if (it.isUser) ChatRole.User else ChatRole.Assistant,
                                    content = it.text
                                )
                            }

                            userInput = ""
                            if(currentInput.first() == '@') {
                                scope.launch {
                                    isLoading = true
                                    try {
                                        val chatCompletionRequest = ChatCompletionRequest(
                                            model = ModelId("gpt-3.5-turbo"),
                                            messages = chatHistory
                                        )
                                        val completion = openai.chatCompletion(chatCompletionRequest)
                                        val replyText = completion.choices.first().message.content ?: "응답이 없습니다."
                                        val llmMessage = AppChatMessage(replyText, false)
                                        messages = messages + llmMessage

                                    } catch (e: Exception) {
                                        val errorMessage = AppChatMessage("오류 발생: ${e.message}", false)
                                        messages = messages + errorMessage
                                        e.printStackTrace()
                                    } finally {
                                        isLoading = false
                                    }
                                }
                            }
                            else {
                                val response = AppChatMessage(currentInput, false)
                                messages = messages + response
                            }
                        }
                    },
                    enabled = !isLoading
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