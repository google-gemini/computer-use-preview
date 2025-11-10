package com.example.myllm

// UI와 Service 간의 통신을 위한 상수 정의
object AccessibilityActions {

    // 1. 방송(Broadcast)의 고유 이름
    // (이 이름이 일치해야만 서비스가 응답합니다)
    const val ACTION_PERFORM_GESTURE = "com.example.myllm.ACTION_PERFORM_GESTURE"

    // 2. 어떤 동작을 할지 구분하는 키
    const val GESTURE_TYPE = "GESTURE_TYPE"

    // 3. 동작의 종류
    const val GESTURE_CLICK = "CLICK"
    const val GESTURE_TYPE_TEXT = "TYPE_TEXT"
    const val GESTURE_SCROLL = "SCROLL"
    const val GESTURE_GO_BACK = "GO_BACK"
    const val GESTURE_OPEN_APP = "OPEN_APP"

    const val GESTURE_GO_HOME = "GO_HOME"
    const val GESTURE_SCROLL_TO_TEXT = "SCROLL_TO_TEXT"
    const val GESTURE_LONG_PRESS = "LONG_PRESS"

    // 4. 동작에 필요한 데이터를 담을 키
    const val EXTRA_X = "EXTRA_X"
    const val EXTRA_Y = "EXTRA_Y"
    const val EXTRA_TEXT = "EXTRA_TEXT"
    const val EXTRA_SCROLL_UP = "EXTRA_SCROLL_UP"
    const val EXTRA_PACKAGE_NAME = "EXTRA_PACKAGE_NAME"
}