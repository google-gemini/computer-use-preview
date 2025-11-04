package com.example.myllm

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.Rect
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.ClipboardManager
import android.content.ClipData
import android.os.Bundle
import android.content.Context.RECEIVER_NOT_EXPORTED
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch


class MyClickService : AccessibilityService() {

    private val serviceScope = CoroutineScope(Dispatchers.Main)

    private val gestureReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action == AccessibilityActions.ACTION_PERFORM_GESTURE) {
                when (intent.getStringExtra(AccessibilityActions.GESTURE_TYPE)) {

                    AccessibilityActions.GESTURE_CLICK -> {
                        val x = intent.getFloatExtra(AccessibilityActions.EXTRA_X, 0f)
                        val y = intent.getFloatExtra(AccessibilityActions.EXTRA_Y, 0f)
                        Log.d("MyClickService", "명령 수신: 클릭 ($x, $y)")
                        clickAt(x, y)
                    }

                    AccessibilityActions.GESTURE_TYPE_TEXT -> {
                        val text = intent.getStringExtra(AccessibilityActions.EXTRA_TEXT) ?: ""
                        val x = intent.getFloatExtra(AccessibilityActions.EXTRA_X, 0f)
                        val y = intent.getFloatExtra(AccessibilityActions.EXTRA_Y, 0f)
                        Log.d("MyClickService", "명령 수신: 클릭 ($x, $y) 후 타이핑 ($text)")
                        clickAndTypeText(x, y, text)
                    }

                    AccessibilityActions.GESTURE_SCROLL -> {
                        val scrollUp = intent.getBooleanExtra(AccessibilityActions.EXTRA_SCROLL_UP, true)
                        val direction = if (scrollUp) "위로" else "아래로"
                        Log.d("MyClickService", "명령 수신: 스크롤 ($direction)")
                        performScroll(scrollUp)
                    }

                    AccessibilityActions.GESTURE_GO_BACK -> {
                        Log.d("MyClickService", "명령 수신: 뒤로 가기")
                        performGoBack()
                    }
                }
            }
        }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        Log.d("MyClickService", "서비스 연결됨. UI 명령 수신 대기 시작.")
        val filter = IntentFilter(AccessibilityActions.ACTION_PERFORM_GESTURE)
        registerReceiver(gestureReceiver, filter, RECEIVER_NOT_EXPORTED)
    }

    private fun clickAt(x: Float, y: Float) {
        val path = Path().apply { moveTo(x, y) }
        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(path, 0, 1))

        dispatchGesture(gestureBuilder.build(), object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                Log.d("MyClickService", "클릭 성공: ($x, $y)")
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                Log.d("MyClickService", "클릭 실패")
            }
        }, null)
    }

    private fun clickAndTypeText(x: Float, y: Float, text: String) {
        val path = Path().apply { moveTo(x, y) }
        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(path, 0, 1))

        dispatchGesture(gestureBuilder.build(), object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                Log.d("MyClickService", "클릭 성공: ($x, $y). 0.7초 후 텍스트 입력 시도...")

                serviceScope.launch {
                    delay(700)
                    performSmartInput(x, y, text)
                }
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                Log.e("MyClickService", "클릭 실패. 타이핑 취소됨.")
            }
        }, null)
    }

    // (performSmartInput, findEditableNodeNear, collectAllNodes 함수는 수정 없음)
    private fun performSmartInput(x: Float, y: Float, text: String) {
        serviceScope.launch {
            val root = rootInActiveWindow
            if (root == null) {
                Log.e("MyClickService", "rootInActiveWindow 가 null입니다.")
                return@launch
            }
            var node: AccessibilityNodeInfo? = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
            if (node == null || !node.isEditable) {
                Log.w("MyClickService", "FOCUS_INPUT 실패 → 근처 Editable 탐색 시도")
                node = findEditableNodeNear(x, y)
            }
            if (node == null) {
                Log.e("MyClickService", "입력 필드 탐색 실패")
                return@launch
            }
            Log.d("MyClickService", "입력 필드 발견 (${node.className})")
            val args = Bundle()
            args.putCharSequence(
                AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,
                text
            )
            val setTextOk = node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
            if (setTextOk) {
                Log.d("MyClickService", "ACTION_SET_TEXT 성공 (기존 내용 덮어쓰기 완료)")
            } else {
                Log.w("MyClickService", "ACTION_SET_TEXT 실패 — 붙여넣기(PASTE) fallback 시도")
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("myllm-paste", text)
                clipboard.setPrimaryClip(clip)
                val pasted = node.performAction(AccessibilityNodeInfo.ACTION_PASTE)
                if (pasted) Log.d("MyClickService", "붙여넣기(PASTE) 성공")
                else Log.e("MyClickService", "붙여넣기(PASTE) 실패")
            }
            node.recycle()
        }
    }
    private fun findEditableNodeNear(x: Float, y: Float): AccessibilityNodeInfo? {
        val root = rootInActiveWindow ?: return null
        val nodes = ArrayList<AccessibilityNodeInfo>()
        collectAllNodes(root, nodes)
        var nearest: AccessibilityNodeInfo? = null
        var minDist = Float.MAX_VALUE
        for (node in nodes) {
            if (node.isEditable) {
                val rect = Rect()
                node.getBoundsInScreen(rect)
                val dx = rect.centerX() - x
                val dy = rect.centerY() - y
                val dist = dx * dx + dy * dy
                if (dist < minDist) {
                    minDist = dist
                    nearest = node
                }
            }
        }
        return nearest
    }
    private fun collectAllNodes(node: AccessibilityNodeInfo?, list: MutableList<AccessibilityNodeInfo>) {
        if (node == null) return
        list.add(node)
        for (i in 0 until node.childCount) {
            collectAllNodes(node.getChild(i), list)
        }
    }

    // scroll_at fucnction
    private fun performScroll(scrollUp: Boolean) {
        // 화면 크기를 가져옴
        val metrics = resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels

        // 스크롤 경로 설정 (화면 중앙)
        val centerX = width / 2f
        val startY = height * 0.7f // 화면 70% 지점
        val endY = height * 0.3f   // 화면 30% 지점
        val duration = 300L // 0.3초 동안 스와이프

        val path = Path()

        if (!scrollUp) {
            Log.d("MyClickService", "스와이프 (아래 -> 위) 수행")
            path.moveTo(centerX, startY)
            path.lineTo(centerX, endY)
        } else {
            Log.d("MyClickService", "스와이프 (위 -> 아래) 수행")
            path.moveTo(centerX, endY)
            path.lineTo(centerX, startY)
        }

        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(path, 0, duration))

        dispatchGesture(gestureBuilder.build(), object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                Log.d("MyClickService", "스크롤 성공")
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                Log.e("MyClickService", "스크롤 실패")
            }
        }, null)
    }

    // go_back function
    private fun performGoBack() {
        // AccessibilityService.GLOBAL_ACTION_BACK은 "뒤로 가기"를 의미
        val success = performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK)
        if (success) {
            Log.d("MyClickService", "뒤로 가기(Global Action) 성공")
        } else {
            Log.e("MyClickService", "뒤로 가기(Global Action) 실패")
        }
    }

    override fun onInterrupt() {
        Log.d("MyClickService", "서비스 중단됨. UI 명령 수신 종료.")
        unregisterReceiver(gestureReceiver)
        serviceScope.cancel()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
}