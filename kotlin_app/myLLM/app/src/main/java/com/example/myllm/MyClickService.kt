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
    private var isScrollingToText = false

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

                    AccessibilityActions.GESTURE_OPEN_APP -> {
                        val pkgName = intent.getStringExtra(AccessibilityActions.EXTRA_PACKAGE_NAME) ?: ""
                        Log.d("MyClickService", "명령 수신: 앱 실행 ($pkgName)")
                        performOpenApp(pkgName)
                    }

                    AccessibilityActions.GESTURE_GO_HOME -> {
                        Log.d("MyClickService", "명령 수신: 홈으로 가기")
                        performGoHome()
                    }

                    AccessibilityActions.GESTURE_SCROLL_TO_TEXT -> {
                        val text = intent.getStringExtra(AccessibilityActions.EXTRA_TEXT) ?: ""
                        Log.d("MyClickService", "명령 수신: 텍스트($text) 찾아 스크롤")
                        performScrollToText(text)
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

    // (clickAt, clickAndTypeText, performSmartInput, ... 등등 수정 없음)
    // ... (이전 함수들) ...
    private fun clickAt(x: Float, y: Float) {
        val path = Path().apply { moveTo(x, y) }
        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(path, 0, 1))
        dispatchGesture(gestureBuilder.build(), object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription); Log.d("MyClickService", "클릭 성공: ($x, $y)")
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription); Log.d("MyClickService", "클릭 실패")
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
                super.onCancelled(gestureDescription); Log.e("MyClickService", "클릭 실패. 타이핑 취소됨.")
            }
        }, null)
    }
    private fun performSmartInput(x: Float, y: Float, text: String) {
        serviceScope.launch {
            val root = rootInActiveWindow
            if (root == null) {
                Log.e("MyClickService", "rootInActiveWindow 가 null입니다."); return@launch
            }
            var node: AccessibilityNodeInfo? = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
            if (node == null || !node.isEditable) {
                Log.w("MyClickService", "FOCUS_INPUT 실패 → 근처 Editable 탐색 시도")
                node = findEditableNodeNear(x, y)
            }
            if (node == null) {
                Log.e("MyClickService", "입력 필드 탐색 실패 ❌"); return@launch
            }
            Log.d("MyClickService", "입력 필드 발견 ✅ (${node.className})")
            val args = Bundle()
            args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
            val setTextOk = node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
            if (setTextOk) {
                Log.d("MyClickService", "ACTION_SET_TEXT 성공 ✅ (기존 내용 덮어쓰기 완료)")
            } else {
                Log.w("MyClickService", "ACTION_SET_TEXT 실패 ❌ — 붙여넣기(PASTE) fallback 시도")
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("myllm-paste", text)
                clipboard.setPrimaryClip(clip)
                val pasted = node.performAction(AccessibilityNodeInfo.ACTION_PASTE)
                if (pasted) Log.d("MyClickService", "붙여넣기(PASTE) 성공 ✅")
                else Log.e("MyClickService", "붙여넣기(PASTE) 실패 ❌")
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
        nodes.forEach { it.recycle() }
        return nearest
    }
    private fun collectAllNodes(node: AccessibilityNodeInfo?, list: MutableList<AccessibilityNodeInfo>) {
        if (node == null) return
        list.add(node)
        for (i in 0 until node.childCount) {
            collectAllNodes(node.getChild(i), list)
        }
    }
    private fun performScroll(scrollUp: Boolean) {
        val metrics = resources.displayMetrics
        val width = metrics.widthPixels; val height = metrics.heightPixels
        val centerX = width / 2f
        val startY = height * 0.7f; val endY = height * 0.3f
        val duration = 300L; val path = Path()
        if (scrollUp) {
            Log.d("MyClickService", "스와이프 (아래 -> 위) 수행"); path.moveTo(centerX, startY); path.lineTo(centerX, endY)
        } else {
            Log.d("MyClickService", "스와이프 (위 -> 아래) 수행"); path.moveTo(centerX, endY); path.lineTo(centerX, startY)
        }
        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(path, 0, duration))
        dispatchGesture(gestureBuilder.build(), object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription); Log.d("MyClickService", "스크롤 성공")
            }
            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription); Log.e("MyClickService", "스크롤 실패")
            }
        }, null)
    }
    private fun performGoBack() {
        val success = performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK)
        if (success) Log.d("MyClickService", "뒤로 가기(Global Action) 성공")
        else Log.e("MyClickService", "뒤로 가기(Global Action) 실패")
    }
    private fun performOpenApp(packageName: String) {
        if (packageName.isBlank()) {
            Log.e("MyClickService", "앱 실행 실패: 패키지 이름이 비어있습니다."); return
        }
        val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
        Log.d("MyClickService", "packageName $packageName")
        if (launchIntent != null) {
            launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            try {
                startActivity(launchIntent)
                Log.d("MyClickService", "앱 실행 성공: $packageName")
            } catch (e: Exception) {
                Log.e("MyClickService", "앱 실행 중 예외 발생", e)
            }
        } else {
            Log.e("MyClickService", "앱 실행 실패: '$packageName' 앱을 찾을 수 없습니다.")
        }
    }
    private fun performGoHome() {
        val success = performGlobalAction(AccessibilityService.GLOBAL_ACTION_HOME)
        if (success) Log.d("MyClickService", "홈으로 가기(Global Action) 성공")
        else Log.e("MyClickService", "홈으로 가기(Global Action) 실패")
    }

    // ⭐️ [수정] "포함(contains)" 검색을 하도록 로직 변경
    private fun findTextOnScreen(searchText: String): Boolean {
        if (searchText.isBlank()) return false
        val root = rootInActiveWindow
        if (root == null) {
            Log.w("MyClickService", "findTextOnScreen: rootInActiveWindow가 null입니다.")
            return false
        }
        val allNodes = ArrayList<AccessibilityNodeInfo>()
        collectAllNodes(root, allNodes)
        var found = false
        for (node in allNodes) {
            val nodeText = node.text?.toString()
            val nodeContentDesc = node.contentDescription?.toString()
            if (nodeText != null && nodeText.contains(searchText, ignoreCase = true)) {
                Log.d("MyClickService", "findTextOnScreen: 텍스트('$nodeText')에서 '$searchText' 발견!")
                found = true
                break
            }
            if (nodeContentDesc != null && nodeContentDesc.contains(searchText, ignoreCase = true)) {
                Log.d("MyClickService", "findTextOnScreen: 내용설명('$nodeContentDesc')에서 '$searchText' 발견!")
                found = true
                break
            }
        }
        allNodes.forEach { it.recycle() }
        return found
    }

    private fun performScrollToText(text: String) {
        if (isScrollingToText) {
            Log.w("MyClickService", "이미 텍스트 검색 스크롤이 진행 중입니다.")
            return
        }
        if (text.isBlank()) {
            Log.w("MyClickService", "검색할 텍스트가 비어있습니다.")
            return
        }

        isScrollingToText = true

        serviceScope.launch {
            val maxAttempts = 10

            for (attempt in 1..maxAttempts) {
                // 1. 현재 화면에서 텍스트 검색
                if (findTextOnScreen(text)) {
                    Log.d("MyClickService", "텍스트 찾기 성공!: '$text'")
                    break // 루프 탈출
                }

                // 2. 텍스트를 못 찾았으면, '더 스크롤할 수 있는지' 확인
                val root = rootInActiveWindow
                if (root == null) {
                    Log.e("MyClickService", "rootInActiveWindow is null. 중지.")
                    break
                }

                val allNodes = ArrayList<AccessibilityNodeInfo>()
                collectAllNodes(root, allNodes)

                // ⭐️ "아래로 스크롤"(FORWARD)이 가능한 노드가 하나라도 있는지 확인
                val canScrollDown = allNodes.any {
                    it.isScrollable && it.actionList.any { action ->
                        action.id == AccessibilityNodeInfo.ACTION_SCROLL_FORWARD
                    }
                }

                allNodes.forEach { it.recycle() } // 노드 정리

                // 3. 더 이상 스크롤할 수 없으면 루프 탈출
                if (!canScrollDown) {
                    Log.w("MyClickService", "텍스트를 찾지 못했고, 더 이상 스크롤할 수 없습니다.")
                    break // 루프 탈출
                }

                // 4. 스크롤이 가능하면, 스크롤 실행
                Log.d("MyClickService", "시도 ${attempt}/${maxAttempts}: 텍스트('$text') 못 찾음. 스크롤 실행.")
                performScroll(true) // (true = 아래로 스크롤)

                delay(1000) // 스크롤 애니메이션 대기
            }

            // 5. 루프가 끝나면(성공했든, 바닥에 도달했든, 타임아웃됐든) 플래그 리셋
            isScrollingToText = false

            // (최종 확인 사살)
            if (!findTextOnScreen(text)) {
                Log.e("MyClickService", "텍스트 찾기 최종 실패: '$text'를 찾을 수 없습니다.")
            }
        }
    }

    override fun onInterrupt() {
        Log.d("MyClickService", "서비스 중단됨. UI 명령 수신 종료.")
        unregisterReceiver(gestureReceiver)
        serviceScope.cancel()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
}