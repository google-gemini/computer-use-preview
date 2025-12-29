package com.example.myllm.data

import android.view.accessibility.AccessibilityNodeInfo

sealed class Action {
    data class ClickAt(val x: Float, val y: Float) : Action()

    data class PerformLongPress(val x: Float, val y: Float) : Action()

    data class ClickAndTypeText(val x: Float, val y: Float, val text: String) : Action()

    data class PerformSmartInput(val x: Float, val y: Float, val text: String) : Action()

    data class FindEditableNodeNear(val x: Float, val y: Float) : Action()

    data class CollectAllNodes(val node: AccessibilityNodeInfo?, val list: MutableList<AccessibilityNodeInfo>) : Action()

    data class PerformScroll(val scrollUp: Boolean) : Action()

    data class PerformHorizontalSwipe(val swipeRight: Boolean) : Action()

    object PerformGoBack : Action()

    data class PerformOpenApp(val packageName: String) : Action()

    object PerformGoHome : Action()

    data class FindTextOnScreen(val searchText: String) : Action()

    data class PerformScrollToText(val text: String) : Action()

    data class PerformWait(val durationMs: Long) : Action()

    data class PerformMacro(val commands: List<String>) : Action()
}