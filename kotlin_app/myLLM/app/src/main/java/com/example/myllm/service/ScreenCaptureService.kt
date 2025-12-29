package com.example.myllm.service

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.DisplayMetrics
import android.util.Log
import android.view.WindowManager
import androidx.core.app.NotificationCompat
import com.aallam.openai.client.Chat
import com.example.myllm.R
import com.example.myllm.network.NetworkClient
import com.example.myllm.repository.ChatRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicBoolean

// 이 서비스는 화면 캡처를 위해 Foreground Service로 실행되어야 한다.
class ScreenCaptureService : Service() {

    private val TAG = "CaptureService"
    private val NOTIFICATION_CHANNEL_ID = "ScreenCaptureChannel"
    private val NOTIFICATION_ID = 101

    // MediaProjection 관련 변수
    private var mediaProjectionManager: MediaProjectionManager? = null
    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null

    // 화면 크기 및 DPI 정보
    private var screenWidth: Int = 0
    private var screenHeight: Int = 0
    private var screenDensityDpi: Int = 0

    private val chatRepository: ChatRepository = ChatRepository()

    // 네트워크 전송용 코루틴 스코프
    private val serviceScope = CoroutineScope(Dispatchers.IO)

    // 현재 캡처 및 전송 작업 중인지 확인하는 플래그
    // atomic하게 CAS 실행
    private val isCapturing = AtomicBoolean(false)


    companion object {
        // Activity에서 서비스로 MediaProjection 권한 결과를 전달하기 위한 키
        const val EXTRA_RESULT_DATA = "extra_result_data"
        // 캡처 후 서버에 전송할 현재 앱 컨텍스트 (Activity 이름 등)
        const val EXTRA_ACTIVITY_CONTEXT = "extra_activity_context"

        // Activity에서 서비스 시작 시 사용할 Intent 생성 함수
        fun getStartIntent(context: Context, data: Intent?, activityContext: String): Intent {
            return Intent(context, ScreenCaptureService::class.java).apply {
                putExtra(EXTRA_RESULT_DATA, data)
                putExtra(EXTRA_ACTIVITY_CONTEXT, activityContext)
            }
        }
    }

    // windowManager 초기화(화면 정보 초기화)
    override fun onCreate() {
        super.onCreate()
        mediaProjectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager

        // 화면 크기 정보 초기화
        val windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        val metrics = DisplayMetrics()

        screenDensityDpi = resources.configuration.densityDpi
        // 최신 API 버전에 따라 다른 방식 사용
        // 최신 api(버전 30이상) => DisplayMetrics 사용
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            windowManager.currentWindowMetrics.bounds.let {
                screenWidth = it.width()
                screenHeight = it.height()
            }
            screenDensityDpi = resources.configuration.densityDpi
        } else {
            @Suppress("DEPRECATION")
            windowManager.defaultDisplay.getMetrics(metrics)
            screenWidth = metrics.widthPixels
            screenHeight = metrics.heightPixels
            screenDensityDpi = metrics.densityDpi
        }

        startForeground(NOTIFICATION_ID, createNotification())
    }

    // isCapturing 변수로 캡쳐 실행
    // false: 캡쳐, true면 캡쳐 중
    // MediaProjection 객체 생성해서 캡쳐
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val resultData: Intent? = intent?.getParcelableExtra(EXTRA_RESULT_DATA)
        val activityContext: String = intent?.getStringExtra(EXTRA_ACTIVITY_CONTEXT) ?: "UnknownApp"

        if (resultData == null) {
            Log.e(TAG, "MediaProjection Intent data is null.")
            stopSelf()
            return START_NOT_STICKY
        }

        if (isCapturing.compareAndSet(false, true)) {

            // MediaProjection 객체를 생성
            mediaProjection = mediaProjectionManager?.getMediaProjection(
                Activity.RESULT_OK,
                resultData
            )

            // 안드로이드 14(API 34) 이상에서 registerCallback 등록 안하면 시스템에서 앱 강제 종료함
            mediaProjection?.registerCallback(object :MediaProjection.Callback(){
                override fun onStop(){
                    super.onStop()
                    virtualDisplay?.release()
                }
            }, Handler(Looper.getMainLooper()))

            if (mediaProjection != null) {
                // 실제 캡처 및 업로드 로직 실행
                captureScreenAndUpload(activityContext)
            } else {
                Log.e(TAG, "MediaProjection failed to start.")
                isCapturing.set(false)
                stopSelf()
            }
        } else {
            Log.w(TAG, "Capture already in progress, ignoring new command.")
        }

        return START_NOT_STICKY
    }

    // 캡처, 변환, 전송
    private fun captureScreenAndUpload(activityContext: String) {
        // ImageReader 설정: RGB_888(컬러) 포맷 사용
        // 마지막 인자는 최대 이미지 수, 여기서는 1
        imageReader = ImageReader.newInstance(
            screenWidth, screenHeight,
            PixelFormat.RGBA_8888, 1
        )

        // VirtualDisplay 생성
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            "ScreenCapture",
            screenWidth, screenHeight,
            screenDensityDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface,
            null,
            null // Handler
        )

        // ImageReader의 리스너 설정 (캡처 완료 시 호출)
        // Main Looper에서 실행되도록 Handler 지정
        imageReader?.setOnImageAvailableListener({ reader ->
            // 캡처 완료 후 리스너 해제 및 리소스 정리
            reader.setOnImageAvailableListener(null, null)

            val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener

            // Image를 Bitmap으로 변환
            val bitmap = processImage(image)
            image.close()
            cleanupResources() // 캡처 완료 후 리소스 정리

            if (bitmap != null) {
                // [Repository] 네트워크 전송용으로 변환 후 업로드
                serviceScope.launch {
                    chatRepository.uploadScreenCapture(bitmap, activityContext)
                    isCapturing.set(false)
                    stopSelf()
                }
            } else {
                isCapturing.set(false)
                Log.e(TAG, "Bitmap is null, upload skipped.")
            }
        }, Handler(Looper.getMainLooper())) // Main Looper 핸들러 사용
    }

    // 서비스 리소스 정리
    private fun cleanupResources() {
        virtualDisplay?.release()
        mediaProjection?.stop()
        imageReader?.close()
        virtualDisplay = null
        mediaProjection = null
        imageReader = null
    }

    override fun onDestroy() {
        super.onDestroy()
        cleanupResources()
        Log.i(TAG, "ScreenCaptureService onDestroy")
    }

    // 바인드 x
    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    private fun processImage(image: Image): Bitmap?{
        return try {
            val planes = image.planes
            val buffer: ByteBuffer = planes[0].buffer
            val pixelStride = planes[0].pixelStride
            val rowStride = planes[0].rowStride
            val rowPadding = rowStride - pixelStride * screenWidth

            val bmp = Bitmap.createBitmap(screenWidth + rowPadding / pixelStride, screenHeight, Bitmap.Config.ARGB_8888)
            bmp.copyPixelsFromBuffer(buffer)

            // 실제 이미지 영역만 잘라내기
            Bitmap.createBitmap(bmp, 0, 0, screenWidth, screenHeight)
        } catch (e: Exception) {
            Log.e(TAG, "Image to Bitmap conversion failed: ${e.message}", e)
            null
        }
    }

    // Foreground Service를 위한 알림 생성
    private fun createNotification(): Notification {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "화면 캡처 서비스",
                NotificationManager.IMPORTANCE_LOW
            )
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(channel)
        }

        return NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("Agent AI 서비스")
            .setContentText("백그라운드에서 화면 캡처 및 분석을 준비 중입니다.")
            .setSmallIcon(R.drawable.ic_launcher_foreground) // 프로젝트에 맞는 아이콘 리소스로 변경 필요
            .build()
    }
}