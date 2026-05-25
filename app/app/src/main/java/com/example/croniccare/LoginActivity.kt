package com.example.croniccare

import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.example.croniccare.data.models.LoginRequest
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityLoginBinding
import com.example.croniccare.utils.SessionManager
import kotlinx.coroutines.launch

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        binding.btnLogin.setOnClickListener { attemptLogin() }

        binding.etPassword.setOnEditorActionListener { _, _, _ ->
            attemptLogin()
            true
        }
    }

    private fun attemptLogin() {
        val dni = binding.etDni.text?.toString()?.trim() ?: ""
        val password = binding.etPassword.text?.toString() ?: ""

        binding.tilDni.error = null
        binding.tilPassword.error = null

        if (dni.isEmpty()) {
            binding.tilDni.error = getString(R.string.error_dni_empty)
            return
        }
        if (password.isEmpty()) {
            binding.tilPassword.error = getString(R.string.error_password_empty)
            return
        }

        setLoading(true)

        lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.login(LoginRequest(dni, password))
                if (response.isSuccessful && response.body() != null) {
                    val loginData = response.body()!!
                    if (loginData.role == "paciente") {
                        session.saveSession(loginData)
                        startActivity(Intent(this@LoginActivity, DashboardActivity::class.java))
                        finish()
                    } else {
                        binding.tilDni.error = "Esta app es para pacientes"
                    }
                } else {
                    binding.tilPassword.error = getString(R.string.error_login_failed)
                }
            } catch (e: Exception) {
                binding.tilPassword.error = getString(R.string.error_network)
            } finally {
                setLoading(false)
            }
        }
    }

    private fun setLoading(loading: Boolean) {
        binding.btnLogin.isEnabled = !loading
        binding.progressLogin.visibility = if (loading) View.VISIBLE else View.GONE
        binding.btnLogin.text = if (loading) getString(R.string.login_loading) else getString(R.string.btn_login)
    }
}
