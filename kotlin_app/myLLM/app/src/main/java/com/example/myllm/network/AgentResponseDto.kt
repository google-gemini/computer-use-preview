package com.example.myllm.network

import kotlinx.serialization.Serializable

@Serializable
data class AgentResponseDto(
    /**
     * /chat/query
     * {"type": "RESPONSE", "message": self.final_reasoning}
     * {'type': 'REQUIRE_SCREENSHOT', 'message': '작업을 위해 현재 화면 스크린샷이 필요합니다. 전송해주세요.'}
     *
     * /chat/step
     * {
     *    'type': 'ACTION',
     *    'action': 'type_text_at',
     *    'args': {'text': '내일 날씨', 'x': 450, 'y': 240, 'press_enter': True}
     *  } - 일반 조작 명령
     * {
     *    'type': 'RESPONSE',
     *    'message': '\n스크롤하니 요일별 날씨가 보입니다. ~~'
     *  } - 최종 응답
     * {
     *    'type': 'ERROR',
     *    'message': "Model generation error: 400 ~~"
     * } - 에러
     * */

    val type: String,
    val message: String? = null,
    val action: String? = null,
    val args: Map<String, String>? = null
)
