package com.example.croniccare.utils

import android.view.View
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updatePadding

fun View.applyStatusBarTopPadding() {
    val initialTop = paddingTop
    ViewCompat.setOnApplyWindowInsetsListener(this) { view, insets ->
        val top = insets.getInsets(WindowInsetsCompat.Type.statusBars()).top
        view.updatePadding(top = initialTop + top)
        insets
    }
    ViewCompat.requestApplyInsets(this)
}

fun View.applyNavBarBottomPadding() {
    val initialBottom = paddingBottom
    ViewCompat.setOnApplyWindowInsetsListener(this) { view, insets ->
        val bottom = insets.getInsets(WindowInsetsCompat.Type.navigationBars()).bottom
        view.updatePadding(bottom = initialBottom + bottom)
        insets
    }
    ViewCompat.requestApplyInsets(this)
}

fun View.applySystemBarsPadding() {
    val initialTop = paddingTop
    val initialBottom = paddingBottom
    ViewCompat.setOnApplyWindowInsetsListener(this) { view, insets ->
        val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
        view.updatePadding(top = initialTop + bars.top, bottom = initialBottom + bars.bottom)
        insets
    }
    ViewCompat.requestApplyInsets(this)
}
