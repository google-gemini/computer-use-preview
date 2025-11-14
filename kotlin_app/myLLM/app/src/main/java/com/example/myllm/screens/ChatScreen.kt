package com.example.myllm.screens // ⬅️ [중요] 패키지 선언

import android.content.Context
import android.util.Log
import androidx.annotation.DrawableRes
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.aallam.openai.api.chat.ChatMessage
import com.aallam.openai.api.chat.ChatRole
import com.aallam.openai.client.OpenAI
import com.example.myllm.BuildConfig
import com.example.myllm.R
import com.example.myllm.data.AppChatMessage // ⬅️ [중요] import 경로
import com.example.myllm.network.AgentRequest
import com.example.myllm.network.RetrofitClient
import com.example.myllm.ui.theme.MyLLMTheme
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream
import java.io.InputStream
import kotlin.collections.listOf
import kotlin.collections.plus

// 채팅 화면 Composable
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(navController: NavController) {
    var userInput by remember { mutableStateOf("") }
    var messages by remember { mutableStateOf(listOf<AppChatMessage>()) }
    var isLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    val context = LocalContext.current

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
                            // append message list
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
                                        val request = AgentRequest(
                                            userId = "Hong-GilDong",
                                            message = currentInput.substring(1)
                                        )
                                        Log.i("AgentRequest", "Chat Sending request: ${request.toString()}")
                                        val agentResponse = RetrofitClient.service.sendMessage(request)
                                        val response = AppChatMessage(agentResponse.toString(), false)
                                        messages = messages + response
                                    } catch (e: Exception) {
                                        Log.e("AgentRequest", "Chat 오류: ${e.message}", e)
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
                    enabled = userInput.isNotBlank()
                ) {
                Text("텍스트 전송")
                }
                Button(
                    onClick = {
                        scope.launch {
                            try {
                                Log.d("AgentRequest", "Observation 사진 데이터 업로드 시작")

                                // MultipartBody.Part 생성
                                val filePart = createMultipartImagePart(
                                    context=context,
                                    drawableId = R.drawable.sample_screenshot
                                )

                                // 앱 상태 XML
                                val contextstr = "<state><app name='WeatherApp'/></state>"
                                // 상태 XML RequestBody 생성 (텍스트 데이터는 plain/text로 전송)
                                val contextBody = contextstr.toRequestBody("text/plain".toMediaTypeOrNull())

                                // 통신 호출
                                val agentResponse = RetrofitClient.service.uploadObservation(filePart, contextBody)
                                val response = AppChatMessage(agentResponse.toString(), false)
                                messages = messages + response
                                response
                            } catch (e: Exception) {
                                Log.e("AgentRequest", "File Upload 통신 오류: ${e.message}", e)
                            } finally {
                                isLoading = false
                            }
                        }
                    }
                ) {
                    Text("사진 전송")
                }
            }
        }
    }
}

fun createMultipartImagePart(
    context: Context,
    @DrawableRes drawableId: Int, // 리소스 ID (R.drawable.sample_screenshot)
    partName: String = "imagePart", // 서버가 기대하는 파트 이름 ("imagePart")
    fileName: String = "sample_screenshot.jpg", // 서버에 표시될 파일 이름
    mediaType: String = "image/jpeg" // 파일의 MIME 타입 (JPEG)
): MultipartBody.Part {
    // 리소스에서 InputStream을 얻음.
    val inputStream: InputStream = context.resources.openRawResource(drawableId)

    // InputStream의 내용을 ByteArray로 변환.
    val byteBuffer = ByteArrayOutputStream()
    val buffer = ByteArray(1024)
    var len: Int
    while (inputStream.read(buffer).also { len = it } != -1) {
        byteBuffer.write(buffer, 0, len)
    }
    val imageBytes = byteBuffer.toByteArray()

    // 바이트 배열을 RequestBody로 변환. (MIME 타입 명시)
    val requestBody = imageBytes.toRequestBody(mediaType.toMediaTypeOrNull(), 0, imageBytes.size)

    // MultipartBody.Part 객체 생성 및 반환합니다.
    // 첫 번째 인수는 서버가 기대하는 이름 ("imagePart"), 두 번째는 파일 이름, 세 번째는 RequestBody입니다.
    return MultipartBody.Part.createFormData(partName, fileName, requestBody)
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