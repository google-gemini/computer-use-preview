package com.example.myllm.service

import java.util.UUID

data class User(val id: UUID, val name: String = "Hong-GilDong")

object UserService {
    private lateinit var currentUser: User

    fun initializeUser() {
        // 서버 응답이나 저장된 데이터를 기반으로 초기화.
        // 현재는 랜덤 ID 사용.
        currentUser = User(UUID.randomUUID(), "Hong-GilDong")
    }

    fun getUser(): User {
        if (!::currentUser.isInitialized) {
            // 초기화되지 않은 경우 처리 (강제 초기화 또는 예외 발생)
            initializeUser()
        }
        return currentUser
    }

    fun getUserId(): String {
        return getUser().id.toString()
    }

    fun updateUserName(newName: String) {
        // data class의 copy 기능을 사용하여 불변성을 유지하면서 업데이트
        currentUser = currentUser.copy(name = newName)
    }
}