package com.example.myllm.data.network

import kotlinx.serialization.Serializable

@Serializable
data class FunctionCallDto(
    // 호출 함수 이름 {"type_test_at"}
    var name: String,
    // {"app_name": "WeatherApp"}, {"x": "100", "y": "200", "input": "Seoul"}
    var args: Map<String, String>
)