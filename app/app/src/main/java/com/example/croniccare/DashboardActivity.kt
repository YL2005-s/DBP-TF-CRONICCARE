package com.example.croniccare

import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.adapters.MetricaAdapter
import com.example.croniccare.adapters.PlanAdapter
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityDashboardBinding
import com.example.croniccare.utils.SessionManager
import kotlinx.coroutines.launch

class DashboardActivity : AppCompatActivity() {

    private lateinit var binding: ActivityDashboardBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDashboardBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        setupHeader()
        setupBottomNav()
        setupListeners()
        loadData()
    }

    private fun setupHeader() {
        binding.tvNombrePaciente.text = session.getNombreCompleto()
        binding.tvEnfermedad.text = session.getEnfermedadDisplay()
    }

    private fun setupBottomNav() {
        binding.bottomNav.selectedItemId = R.id.nav_dashboard
        binding.bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_registrar -> {
                    startActivity(Intent(this, RegistrarMetricaActivity::class.java))
                    false
                }
                R.id.nav_historial -> {
                    startActivity(Intent(this, HistorialActivity::class.java))
                    false
                }
                R.id.nav_plan -> {
                    startActivity(Intent(this, PlanCuidadoActivity::class.java))
                    false
                }
                else -> true
            }
        }
    }

    private fun setupListeners() {
        binding.btnLogout.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("Cerrar sesión")
                .setMessage("¿Estás seguro que deseas salir?")
                .setPositiveButton("Salir") { _, _ ->
                    session.clearSession()
                    startActivity(Intent(this, LoginActivity::class.java))
                    finish()
                }
                .setNegativeButton("Cancelar", null)
                .show()
        }

        binding.btnVerHistorial.setOnClickListener {
            startActivity(Intent(this, HistorialActivity::class.java))
        }

        binding.btnVerPlan.setOnClickListener {
            startActivity(Intent(this, PlanCuidadoActivity::class.java))
        }
    }

    private fun loadData() {
        val token = session.getAuthToken()

        lifecycleScope.launch {
            try {
                val metricasResponse = RetrofitClient.instance.getMisMetricas(token)
                if (metricasResponse.isSuccessful) {
                    val metricas = metricasResponse.body() ?: emptyList()
                    val recientes = metricas.take(3)

                    if (recientes.isEmpty()) {
                        binding.tvSinMetricas.visibility = View.VISIBLE
                        binding.rvMetricasRecientes.visibility = View.GONE
                    } else {
                        binding.tvSinMetricas.visibility = View.GONE
                        binding.rvMetricasRecientes.visibility = View.VISIBLE
                        binding.rvMetricasRecientes.layoutManager = LinearLayoutManager(this@DashboardActivity)
                        binding.rvMetricasRecientes.adapter = MetricaAdapter(recientes)
                    }

                    // Determine status from most recent metric
                    val hasAlerta = recientes.any { it.alerta }
                    updateEstado(hasAlerta)
                }
            } catch (e: Exception) {
                binding.tvSinMetricas.visibility = View.VISIBLE
            }
        }

        lifecycleScope.launch {
            try {
                val planResponse = RetrofitClient.instance.getMiPlan(token)
                if (planResponse.isSuccessful) {
                    val plan = planResponse.body() ?: emptyList()

                    if (plan.isEmpty()) {
                        binding.tvSinPlan.visibility = View.VISIBLE
                        binding.rvPlanHoy.visibility = View.GONE
                    } else {
                        binding.tvSinPlan.visibility = View.GONE
                        binding.rvPlanHoy.visibility = View.VISIBLE
                        binding.rvPlanHoy.layoutManager = LinearLayoutManager(this@DashboardActivity)
                        binding.rvPlanHoy.adapter = PlanAdapter(plan.take(3))
                    }
                }
            } catch (e: Exception) {
                binding.tvSinPlan.visibility = View.VISIBLE
            }
        }
    }

    private fun updateEstado(hasAlerta: Boolean) {
        if (hasAlerta) {
            binding.tvEstado.text = getString(R.string.status_riesgo)
            binding.tvEstado.setBackgroundColor(Color.parseColor("#80F57F17"))
        } else {
            binding.tvEstado.text = getString(R.string.status_estable)
            binding.tvEstado.setBackgroundColor(Color.parseColor("#802E7D32"))
        }
    }

    override fun onResume() {
        super.onResume()
        loadData()
        binding.bottomNav.selectedItemId = R.id.nav_dashboard
    }
}
