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
    @SerializedName("fecha_registro") val fechaRegistro: String?
)

data class Metrica(
    val id: Int,
    val tipo: String,
    val valor: Double,
    @SerializedName("valor_diastolica") val valorDiastolica: Double?,
    val alerta: Boolean,
    val fecha: String
)

data class RegistrarMetricaRequest(
    val tipo: String,
    val valor: Double,
    @SerializedName("valor_diastolica") val valorDiastolica: Double? = null
)

data class RegistrarMetricaResponse(
    val id: Int,
    val tipo: String,
    val valor: Double,
    @SerializedName("valor_diastolica") val valorDiastolica: Double?,
    val alerta: Boolean,
    val criticidad: String?,
    val fecha: String,
    val mensaje: String
)

data class Alerta(
    val id: Int,
    val paciente: Int,
    val metrica: Int?,
    val mensaje: String,
    val criticidad: String,
    val resuelta: Boolean,
    val fecha: String
)

data class Prescripcion(
    val id: Int,
    val medicamento: String,
    val dosis: String,
    val via: String,
    @SerializedName("via_display") val viaDisplay: String,
    val frecuencia: String,
    @SerializedName("frecuencia_display") val frecuenciaDisplay: String,
    val indicaciones: String,
    @SerializedName("fecha_inicio") val fechaInicio: String,
    @SerializedName("fecha_fin") val fechaFin: String?,
    val activa: Boolean,
    @SerializedName("medico_nombre") val medicoNombre: String?
)

data class Consulta(
    val id: Int,
    val tipo: String,
    @SerializedName("tipo_display") val tipoDisplay: String,
    val estado: String,
    @SerializedName("estado_display") val estadoDisplay: String,
    @SerializedName("fecha_hora") val fechaHora: String,
    val motivo: String,
    val diagnostico: String,
    val indicaciones: String,
    @SerializedName("proxima_cita") val proximaCita: String?,
    @SerializedName("medico_nombre") val medicoNombre: String?
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
