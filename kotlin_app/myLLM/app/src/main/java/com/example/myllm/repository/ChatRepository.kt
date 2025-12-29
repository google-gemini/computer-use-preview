package com.example.myllm.repository

import android.graphics.Bitmap
import android.util.Log
import com.example.myllm.data.Action
import com.example.myllm.network.AgentResponseDto
import com.example.myllm.network.ApiService
import com.example.myllm.network.NetworkClient
import com.example.myllm.service.ActionController
import com.example.myllm.service.UserService
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream

class ChatRepository(
    private val apiService: ApiService = NetworkClient.service // 기존 싱글톤 사용
) {
    suspend fun processUserMessage(userInput: String): Result<AgentResponseDto> {
        return try {
            // 서버에 텍스트 전송 (Network)
            val response = NetworkClient.service.sendMessage(userInput, UserService.getUserId())
            if(response.isSuccessful){
                val body = response.body()
                if(body != null){
                    if(body.type == "ACTION"){
                        val action = parseAction(body)
                        ActionController.sendAction(action)
                    }
                    Log.i("ChatRepository", "Form 전송 성공: ${response.code()}")
                    Result.success(body)
                } else{
                    Result.failure(Exception("Empty Response Body"))
                }
            }else{
                Log.e("ChatRepository", "Form 전송 실패: ${response.code()}")
                Result.failure(Exception("Error Code: ${response.code()}"))
            }
        } catch (e: Exception) {
            Log.e("ChatRepository", "Chat 오류: ${e.message}", e)
            Result.failure(e)
        }
    }

    private fun parseAction(dto: AgentResponseDto) : Action {
        return when(dto.action){
            "click_at" -> {
                // args가 Map<String, Any> 형태라고 가정할 때의 파싱
                val x = dto.args?.get("x")?.toFloat() ?: 0f
                val y = dto.args?.get("x")?.toFloat() ?: 0f
                Action.ClickAt(x, y)
            }
            "go_home" -> {
                Action.PerformGoHome
            }

            "INPUT" -> {
                val text = dto.args?.get("text") as? String ?: ""
                Log.i("ChatRepository", text)
                Action.ClickAt(0f, 0f)
            }

            else -> Action.ClickAt(0f, 0f)
        }
    }


     // 스크린샷 이미지와 컨텍스트를 서버로 업로드 (Service에서 호출)
    suspend fun uploadScreenCapture(bitmap: Bitmap, activityContext: String): Result<AgentResponseDto> {
        return try {
            // Bitmap을 MultipartBody.Part로 변환
            val filePart = bitmapToMultipartPart(bitmap)

            // Activity 컨텍스트를 포함
            val contextstr = "<state><app name='${activityContext}'/></state>"
            val contextBody = contextstr.toRequestBody("text/plain".toMediaTypeOrNull())
            val sessionIdBody = UserService.getUserId().toRequestBody("text/plain".toMediaTypeOrNull())

            val agentResponse = NetworkClient.service.sendStepMultipart(filePart, contextBody,
                sessionIdBody)

            if(agentResponse.isSuccessful){
                val body = agentResponse.body()
                if(body != null){
                    if (body.type == "ACTION") {
                        ActionController.sendAction(parseAction(body))
                    }
                    Log.i("ChatRepository", "Image Form 전송 성공: ${body.message}")
                    Result.success(body)
                }else{
                    Result.failure(Exception("Empty Response"))
                }
            }else{
                Log.e("ChatViewModel", "Image Form 전송 실패: ${agentResponse.code()}")
                Result.failure(Exception("Upload Failed: ${agentResponse.code()}"))
            }
        } catch (e: Exception) {
            Log.e("ChatViewModel", "스크린샷 업로드 통신 오류: ${e.message}", e)
            Result.failure(e)
        }
    }

    // Bitmap을 네트워크 전송용 Multipart로 변환
    private fun bitmapToMultipartPart(
        bitmap: Bitmap,
        partName: String = "screenshot", // 서버가 기대하는 파트 이름 (FastAPI 예시의 'screenshot')
        fileName: String = "${UserService.getUserId()}_${System.currentTimeMillis()}.jpg",
        mediaType: String = "image/jpeg"
    ): MultipartBody.Part {
        val byteArrayOutputStream = ByteArrayOutputStream()

        // JPEG 포맷으로 압축
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, byteArrayOutputStream)
        val imageBytes = byteArrayOutputStream.toByteArray()

        val requestBody = imageBytes.toRequestBody(mediaType.toMediaTypeOrNull(), 0, imageBytes.size)

        return MultipartBody.Part.createFormData(partName, fileName, requestBody)
    }

}