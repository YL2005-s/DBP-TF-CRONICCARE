package com.example.croniccare.utils

import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.view.View
import java.lang.ref.WeakReference

class ScreenStateManager(
    skeleton: View,
    content: View,
    empty: View? = null,
    private val animDuration: Long = 600L
) {
    private val skeletonRef = WeakReference(skeleton)
    private val contentRef  = WeakReference(content)
    private val emptyRef    = WeakReference(empty)
    private var animator: ObjectAnimator? = null

    fun showLoading() {
        skeletonRef.get()?.visibility = View.VISIBLE
        contentRef.get()?.visibility  = View.GONE
        emptyRef.get()?.visibility    = View.GONE
        startPulse()
    }

    fun showContent() {
        stopPulse()
        skeletonRef.get()?.visibility = View.GONE
        contentRef.get()?.visibility  = View.VISIBLE
        emptyRef.get()?.visibility    = View.GONE
    }

    fun showEmpty() {
        stopPulse()
        skeletonRef.get()?.visibility = View.GONE
        contentRef.get()?.visibility  = View.GONE
        emptyRef.get()?.visibility    = View.VISIBLE
    }

    fun destroy() = stopPulse()

    private fun startPulse() {
        val skeleton = skeletonRef.get() ?: return
        animator?.cancel()
        animator = ObjectAnimator.ofFloat(skeleton, "alpha", 1f, 0.4f).apply {
            duration    = animDuration
            repeatMode  = ValueAnimator.REVERSE
            repeatCount = ValueAnimator.INFINITE
            start()
        }
    }

    private fun stopPulse() {
        animator?.cancel()
        animator = null
        skeletonRef.get()?.alpha = 1f
    }
}
