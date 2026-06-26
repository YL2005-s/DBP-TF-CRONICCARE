package com.example.croniccare.utils

import android.content.Context
import java.text.SimpleDateFormat
import java.util.*

object AdherenciaPrefs {

    private const val PREFS_NAME = "plan_adherencia"

    private fun key(planId: Int): String {
        val hoy = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
        return "cumplimiento_${planId}_$hoy"
    }

    fun loadCompleted(context: Context, allIds: List<Int>): MutableSet<Int> {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return allIds.filter { prefs.getBoolean(key(it), false) }.toMutableSet()
    }

    fun save(context: Context, planId: Int, done: Boolean) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(key(planId), done)
            .apply()
    }
}
