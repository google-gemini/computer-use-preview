package com.example.myllm.data.network

import kotlinx.serialization.Serializable

@Serializable
data class AgentRequest(
    val userId: String,
    val message: String, // 사용자의 현재 발화 (예: "오늘 날씨 어때?")
    val currentContext: String? = null // 현재 앱 상태 요약 (XML 파일이 아닌 텍스트 요약)
)