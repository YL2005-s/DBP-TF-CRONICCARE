package com.example.croniccare.utils

import android.content.Context
import android.content.SharedPreferences
import com.example.croniccare.data.models.LoginResponse
import com.example.croniccare.data.network.RetrofitClient

class SessionManager(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("cronic_care_session", Context.MODE_PRIVATE)

    companion object {
        private const val KEY_TOKEN = "auth_token"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_USERNAME = "username"
        private const val KEY_NOMBRE = "nombre_completo"
        private const val KEY_ROLE = "role"
        private const val KEY_PACIENTE_ID = "paciente_id"
        private const val KEY_ENFERMEDAD = "enfermedad"
        private const val KEY_ENFERMEDAD_DISPLAY = "enfermedad_display"
    }

    fun saveSession(response: LoginResponse) {
        val displayName = response.paciente?.nombre
            ?.takeIf { it.isNotBlank() }
            ?: response.nombreCompleto

        prefs.edit()
            .putString(KEY_TOKEN, response.token)
            .putInt(KEY_USER_ID, response.userId)
            .putString(KEY_USERNAME, response.username)
            .putString(KEY_NOMBRE, displayName)
            .putString(KEY_ROLE, response.role)
            .also { editor ->
                response.paciente?.let {
                    editor.putInt(KEY_PACIENTE_ID, it.id)
                    editor.putString(KEY_ENFERMEDAD, it.enfermedad)
                    editor.putString(KEY_ENFERMEDAD_DISPLAY, it.enfermedadDisplay)
                }
            }
            .apply()

        RetrofitClient.authToken = "Token ${response.token}"
    }

    fun initRetrofitToken() {
        val token = prefs.getString(KEY_TOKEN, null)
        if (!token.isNullOrBlank()) {
            RetrofitClient.authToken = "Token $token"
        }
    }

    fun getNombreCompleto(): String = prefs.getString(KEY_NOMBRE, "Paciente") ?: "Paciente"

    fun getEnfermedadDisplay(): String = prefs.getString(KEY_ENFERMEDAD_DISPLAY, "—") ?: "—"

    fun getEnfermedad(): String = prefs.getString(KEY_ENFERMEDAD, "") ?: ""

    fun getPacienteId(): Int = prefs.getInt(KEY_PACIENTE_ID, -1)

    fun isLoggedIn(): Boolean = prefs.getString(KEY_TOKEN, null) != null

    fun clearSession() {
        prefs.edit().clear().apply()
        RetrofitClient.authToken = ""
    }
}
