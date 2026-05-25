package com.example.croniccare.data.network

import com.example.croniccare.data.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    @POST("api/auth/login/")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @GET("api/mis-metricas/")
    suspend fun getMisMetricas(
        @Header("Authorization") token: String
    ): Response<List<Metrica>>

    @POST("api/registrar-metrica/")
    suspend fun registrarMetrica(
        @Header("Authorization") token: String,
        @Body request: RegistrarMetricaRequest
    ): Response<RegistrarMetricaResponse>

    @GET("api/mi-plan/")
    suspend fun getMiPlan(
        @Header("Authorization") token: String
    ): Response<List<PlanCuidado>>
}
