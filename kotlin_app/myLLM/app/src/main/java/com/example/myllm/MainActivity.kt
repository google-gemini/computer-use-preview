package com.example.myllm

import android.content.Context
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.annotation.DrawableRes
import com.example.myllm.ui.theme.MyLLMTheme
import com.example.myllm.navigation.AppNavigation
import com.example.myllm.network.AgentRequest
import com.example.myllm.network.AgentResponse
import com.example.myllm.network.RetrofitClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream
import java.io.InputStream

class MainActivity : ComponentActivity() {
    // 로그
    private val TAG = "LLMAgentApp"

    // UI 로직 (Button Click 등) 대신 CoroutineScope를 사용합니다.
    private val mainScope = CoroutineScope(Dispatchers.Main)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            MyLLMTheme {
                // 내비게이션 Composable만 호출
                AppNavigation()
            }
        }

        // 새로운 코루틴 생성
        mainScope.launch {
            try {
                // 예시 메세지 Agent에 전송
                val request = AgentRequest(
                    userId = "user-123",
                    message = "오늘 날씨 어때?"
                )
                Log.i(TAG, "Chat Sending request: ${request.toString()}")
                val response = RetrofitClient.service.sendMessage(request)
                handleLlmResponse(response)
            } catch (e: Exception) {
                Log.e(TAG, "Chat 오류: ${e.message}", e)
            }
        }

        mainScope.launch {
            try {
                Log.d(TAG, "Observation 사진 데이터 업로드 시작")

                // MultipartBody.Part 생성
                val filePart = createMultipartImagePart(
                    applicationContext,
                    R.drawable.sample_screenshot
                )

                // 앱 상태 XML
                val contextstr = "<state><app name='WeatherApp'/></state>"
                // 상태 XML RequestBody 생성 (텍스트 데이터는 plain/text로 전송)
                val contextBody = contextstr.toRequestBody("text/plain".toMediaTypeOrNull())

                // 통신 호출
                val response = RetrofitClient.service.uploadObservation(filePart, contextBody)

                // 서버 응답 처리
                handleLlmResponse(response)
            } catch (e: Exception) {
                Log.e(TAG, "File Upload 통신 오류: ${e.message}", e)
            }
        }
    }

    private fun handleLlmResponse(response: AgentResponse) {
        Log.d(TAG, "LLM 응답 수신: Type=${response.type}")
        when (response.type) {
            "text" -> {
                // 일상 대화 처리
                Log.i(TAG, "LLM 텍스트 응답: ${response.textResponse}")
                // TODO: UI에 텍스트 표시
            }
            "function_call" -> {
                // 앱 기능 사용 명령 처리
                val func = response.functionCall
                if (func != null) {
                    Log.w(TAG, "기능 호출 명령 수신: ${func.name}(${func.args})")
                    // TODO: 앱 실제 기능 실행
                }
            }
            else -> {
                Log.e(TAG, "알 수 없는 응답 유형: ${response?.type}")
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
}