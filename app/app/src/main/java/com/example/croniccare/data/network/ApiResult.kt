package com.example.croniccare.data.network

import retrofit2.Response
import java.io.IOException

sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error(val code: Int?, val message: String) : ApiResult<Nothing>()
}

suspend fun <T> safeApiCall(call: suspend () -> Response<T>): ApiResult<T> {
    return try {
        val response = call()
        if (response.isSuccessful) {
            val body = response.body()
            if (body != null) ApiResult.Success(body)
            else ApiResult.Error(response.code(), "Respuesta vacía del servidor")
        } else {
            ApiResult.Error(response.code(), response.message())
        }
    } catch (e: IOException) {
        ApiResult.Error(null, "Sin conexión a internet")
    } catch (e: Exception) {
        ApiResult.Error(null, "Error inesperado")
    }
}
