package com.example.myllm.data // ⬅️ [중요] 패키지 선언

// 메시지 데이터 클래스만 분리
data class AppChatMessage(
    val text: String,
    val isUser: Boolean // true = 사용자, false = LLM
)