package com.example.myllm.network

import kotlinx.serialization.Serializable

@Serializable
data class AgentResponse(
    val type: String,   // "text" (일상대화) 또는 "function_call" (기능사용)
    val textResponse: String? = null,  // type이 "text"일 경우: LLM의 최종 텍스트 응답
    val functionCall: FunctionCall? = null  // type이 "function_call"일 경우: 앱이 실행해야 할 명령
)
