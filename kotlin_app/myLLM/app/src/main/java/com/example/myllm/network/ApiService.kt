package com.example.myllm.network

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

// 일단 테스트용 로컬 서버 링크 사용
private const val BASE_URL = "http://10.0.2.2:8080/api/"

interface ApiService {
    /**
     * 일반 대화 및 기능 호출 요청 전송
     * @param request JSON 형식의 사용자 메시지 및 컨텍스트
     * @return Response<AgentRequest> (텍스트 응답 또는 기능 호출 JSON)
     */
    @POST("chat")
    suspend fun sendMessage(@Body request: AgentRequest): AgentResponse

    /**
     * 스크린샷과 XML 상태 데이터를 서버에 전송
     * @param imagePart 스크린샷 파일 (MultipartBody.Part)
     * @param contextData XML/Intent 상태 정보를 담은 텍스트 부분 (RequestBody)
     * @return Response<AgentRequest> 업로드 성공에 대한 간단한 응답
     */
    @Multipart
    @POST("upload_observation")
    suspend fun uploadObservation(
        @Part imagePart: MultipartBody.Part,
        @Part("context_data") contextData: RequestBody
    ): AgentResponse
}

/*
    RetrofitClient
    매 네트워크 req/res마다 호출되므로 싱글톤 선언
 */
object RetrofitClient{
    // json형태 유연하게
    private val json = Json {
        ignoreUnknownKeys = true // JSON에 정의되지 않은 필드는 무시
        isLenient = true
    }

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val service: ApiService by lazy {
        retrofit.create(ApiService::class.java)
    }
}