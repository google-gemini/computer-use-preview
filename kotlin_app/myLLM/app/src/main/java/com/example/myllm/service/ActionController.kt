package com.example.myllm.service

import com.example.myllm.data.Action
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

object ActionController {
    // ViewModel이 이 Flow에 액션을 던지면, Service가 관찰하다가 실행
    private val _actionFlow = MutableSharedFlow<Action>()
    val actionFlow = _actionFlow.asSharedFlow()

    suspend fun sendAction(action: Action) {
        _actionFlow.emit(action)
    }
}