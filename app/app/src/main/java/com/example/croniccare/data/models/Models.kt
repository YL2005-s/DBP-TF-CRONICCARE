package com.example.croniccare.data.models

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    val username: String,
    val password: String
)

data class LoginResponse(
    val token: String,
    @SerializedName("user_id") val userId: Int,
    val username: String,
    @SerializedName("nombre") val nombreCompleto: String,
    @SerializedName("rol") val role: String,
    val paciente: PacienteInfo?
)

data class PacienteInfo(
    val id: Int,
    val nombre: String,
    val dni: String,
    val enfermedad: String,
    @SerializedName("enfermedad_display") val enfermedadDisplay: String,
    @SerializedName("fecha_registro") val fechaRegistro: String
)

data class Metrica(
    val id: Int,
    val tipo: String,
    val valor: Double,
    val alerta: Boolean,
    val fecha: String
)

data class RegistrarMetricaRequest(
    val tipo: String,
    val valor: Double
)

data class RegistrarMetricaResponse(
    val id: Int,
    val tipo: String,
    val valor: Double,
    val alerta: Boolean,
    val fecha: String,
    val mensaje: String
)

data class PlanCuidado(
    val id: Int,
    val tipo: String,
    @SerializedName("tipo_display") val tipoDisplay: String,
    @SerializedName("tipo_metrica") val tipoMetrica: String?,
    @SerializedName("tipo_metrica_display") val tipoMetricaDisplay: String?,
    val descripcion: String,
    val hora: String,
    val frecuencia: String,
    @SerializedName("frecuencia_display") val frecuenciaDisplay: String,
    val activo: Boolean,
    @SerializedName("fecha_inicio") val fechaInicio: String
)
