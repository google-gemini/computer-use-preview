package com.example.myllm.screens

import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.example.myllm.AccessibilityActions
import com.example.myllm.ui.theme.MyLLMTheme

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TestScreen(navController: NavController) {

    var xPixelClick by remember { mutableStateOf("") }
    var yPixelClick by remember { mutableStateOf("") }
    var xPixelType by remember { mutableStateOf("") }
    var yPixelType by remember { mutableStateOf("") }
    var textToType by remember { mutableStateOf("") }
    var scrollUp by remember { mutableStateOf(true) }
    var targetTextFieldValue by remember { mutableStateOf("") }
    var packageName by remember { mutableStateOf("") }

    var xPixelLong by remember { mutableStateOf("") }
    var yPixelLong by remember { mutableStateOf("") }

    val context = LocalContext.current
    val scrollState = rememberScrollState()

    var textToFind by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("테스트 페이지") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "뒤로 가기")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.Top,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {

            Spacer(modifier = Modifier.height(24.dp))
            Text("권한 설정", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    // "접근성 설정" 화면으로 바로 이동하는 Intent
                    val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                    context.startActivity(intent)
                    println("접근성 설정 바로가기 실행")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("접근성 설정 바로가기")
            }

            Text(
                "테스트 대상",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.fillMaxWidth()
            )
            TextField(
                value = targetTextFieldValue,
                onValueChange = { targetTextFieldValue = it },
                label = { Text("타이핑 타겟") },
                placeholder = { Text("여기에 텍스트가 입력됩니다...") },
                modifier = Modifier
                    .fillMaxWidth()
                    .semantics { contentDescription = "ID:target_text_field" }
            )

            Spacer(modifier = Modifier.height(24.dp))
            HorizontalDivider()
            Spacer(modifier = Modifier.height(24.dp))

            Text(
                "자동화 컨트롤러",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // --- 1. 단순 클릭 섹션 ---
            Text("1. 단순 클릭", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                TextField(
                    value = xPixelClick,
                    onValueChange = { xPixelClick = it },
                    label = { Text("X 픽셀") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
                TextField(
                    value = yPixelClick,
                    onValueChange = { yPixelClick = it },
                    label = { Text("Y 픽셀") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    val x = xPixelClick.toFloatOrNull() ?: 0f
                    val y = yPixelClick.toFloatOrNull() ?: 0f
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_CLICK)
                        putExtra(AccessibilityActions.EXTRA_X, x)
                        putExtra(AccessibilityActions.EXTRA_Y, y)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    println("픽셀 클릭 방송 보냄: ($x, $y)")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("특정 픽셀 클릭")
            }

            Spacer(modifier = Modifier.height(24.dp))

            // --- 2. 입력값 타이핑 섹션 ---
            Text("2. 클릭 후 텍스트 타이핑", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                TextField(
                    value = xPixelType,
                    onValueChange = { xPixelType = it },
                    label = { Text("타겟 X 픽셀") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
                TextField(
                    value = yPixelType,
                    onValueChange = { yPixelType = it },
                    label = { Text("타겟 Y 픽셀") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            TextField(
                value = textToType,
                onValueChange = { textToType = it },
                label = { Text("타이핑할 텍스트") },
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    val x = xPixelType.toFloatOrNull() ?: 0f
                    val y = yPixelType.toFloatOrNull() ?: 0f
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_TYPE_TEXT)
                        putExtra(AccessibilityActions.EXTRA_TEXT, textToType)
                        putExtra(AccessibilityActions.EXTRA_X, x)
                        putExtra(AccessibilityActions.EXTRA_Y, y)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    println("클릭 후 타이핑 방송 보냄: $textToType at ($x, $y)")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("클릭 후 타이핑")
            }

            Spacer(modifier = Modifier.height(24.dp))

            // --- 3. 스크롤 섹션 ---
            Text("3. 스크롤", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                Text(if (scrollUp) "위로" else "아래로")
                Spacer(modifier = Modifier.width(16.dp))
                Switch(
                    checked = scrollUp,
                    onCheckedChange = { scrollUp = it }
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_SCROLL)
                        putExtra(AccessibilityActions.EXTRA_SCROLL_UP, scrollUp)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    val direction = if (scrollUp) "위로" else "아래로"
                    println("스크롤 방송 보냄: $direction")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("스크롤 수행")
            }

            Spacer(modifier = Modifier.height(8.dp))
            TextField(
                value = textToFind,
                onValueChange = { textToFind = it },
                label = { Text("찾을 텍스트 (예: 더미 아이템 25)") },
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_SCROLL_TO_TEXT)
                        putExtra(AccessibilityActions.EXTRA_TEXT, textToFind)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    println("텍스트($textToFind) 찾기 스크롤 방송 보냄")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("이 텍스트까지 스크롤 (아래로)")
            }

            // --- 4. 시스템 액션 ---
            Spacer(modifier = Modifier.height(24.dp))
            Text("4. 시스템 액션", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_GO_BACK)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    println("뒤로 가기 방송 보냄")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("뒤로 가기")
            }

            Spacer(modifier = Modifier.height(8.dp)) // 버튼 사이 간격
            Button(
                onClick = {
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_GO_HOME)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    println("홈으로 가기 방송 보냄")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("홈으로 가기")
            }


            // --- 5. 앱 실행 ---
            Spacer(modifier = Modifier.height(24.dp))
            Text("5. 앱 실행", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
            TextField(
                value = packageName,
                onValueChange = { packageName = it },
                label = { Text("앱 패키지 이름 (예: com.kakao.talk)") },
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_OPEN_APP)
                        putExtra(AccessibilityActions.EXTRA_PACKAGE_NAME, packageName)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    println("앱 실행 방송 보냄: $packageName")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("앱 실행")
            }

            Spacer(modifier = Modifier.height(24.dp))
            Text("7. 롱 클릭", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                TextField(
                    value = xPixelLong,
                    onValueChange = { xPixelLong = it },
                    label = { Text("X 픽셀") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
                TextField(
                    value = yPixelLong,
                    onValueChange = { yPixelLong = it },
                    label = { Text("Y 픽셀") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = {
                    val x = xPixelLong.toFloatOrNull() ?: 0f
                    val y = yPixelLong.toFloatOrNull() ?: 0f
                    val intent = Intent(AccessibilityActions.ACTION_PERFORM_GESTURE).apply {
                        putExtra(AccessibilityActions.GESTURE_TYPE, AccessibilityActions.GESTURE_LONG_PRESS)
                        putExtra(AccessibilityActions.EXTRA_X, x)
                        putExtra(AccessibilityActions.EXTRA_Y, y)
                        setPackage(context.packageName)
                    }
                    context.sendBroadcast(intent)
                    println("롱 클릭 방송 보냄: ($x, $y)")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("특정 픽셀 롱 클릭")
            }

            Spacer(modifier = Modifier.height(48.dp))
            HorizontalDivider()
            Text(
                "스크롤 테스트용 더미 공간",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(top = 16.dp, bottom = 16.dp)
            )
            repeat(30) { index ->
                Text(
                    "더미 아이템 $index",
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp)
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun TestScreenPreview() {
    MyLLMTheme {
        TestScreen(navController = rememberNavController())
    }
}