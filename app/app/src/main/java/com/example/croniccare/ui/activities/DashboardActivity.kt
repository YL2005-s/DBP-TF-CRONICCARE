package com.example.croniccare.ui.activities

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.adapters.MetricaAdapter
import com.example.croniccare.adapters.PlanAdapter
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityDashboardBinding
import com.example.croniccare.utils.SessionManager
import kotlinx.coroutines.launch
import androidx.core.graphics.toColorInt
import com.example.croniccare.MainActivity
import com.example.croniccare.R

class DashboardFragment : Fragment() {

    private var _binding: ActivityDashboardBinding? = null
    private val binding get() = _binding!!
    private lateinit var session: SessionManager

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        session = SessionManager(requireContext())
        setupHeader()
        setupListeners()
        loadData()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupHeader() {
        binding.tvNombrePaciente.text = session.getNombreCompleto()
        binding.tvEnfermedad.text = session.getEnfermedadDisplay()
    }

    private fun setupListeners() {
        binding.btnLogout.setOnClickListener {
            AlertDialog.Builder(requireContext())
                .setTitle("Cerrar sesión")
                .setMessage("¿Estás seguro que deseas salir?")
                .setPositiveButton("Salir") { _, _ ->
                    session.clearSession()
                    (requireActivity() as MainActivity).navigateToLogin()
                }
                .setNegativeButton("Cancelar", null)
                .show()
        }

        binding.btnVerHistorial.setOnClickListener {
            findNavController().navigate(R.id.nav_historial)
        }

        binding.btnVerPlan.setOnClickListener {
            findNavController().navigate(R.id.nav_plan)
        }
    }

    private fun loadData() {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val metricasResponse = RetrofitClient.instance.getMisMetricas()
                if (metricasResponse.isSuccessful) {
                    val metricas = metricasResponse.body() ?: emptyList()
                    val recientes = metricas.take(3)

                    if (recientes.isEmpty()) {
                        binding.tvSinMetricas.visibility = View.VISIBLE
                        binding.rvMetricasRecientes.visibility = View.GONE
                    } else {
                        binding.tvSinMetricas.visibility = View.GONE
                        binding.rvMetricasRecientes.visibility = View.VISIBLE
                        binding.rvMetricasRecientes.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvMetricasRecientes.adapter = MetricaAdapter(recientes)
                    }

                    val hasAlerta = recientes.any { it.alerta }
                    updateEstado(hasAlerta)
                }
            } catch (_: Exception) {
                if (_binding != null) binding.tvSinMetricas.visibility = View.VISIBLE
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val planResponse = RetrofitClient.instance.getMiPlan()
                if (planResponse.isSuccessful) {
                    val plan = planResponse.body() ?: emptyList()

                    if (plan.isEmpty()) {
                        binding.tvSinPlan.visibility = View.VISIBLE
                        binding.rvPlanHoy.visibility = View.GONE
                    } else {
                        binding.tvSinPlan.visibility = View.GONE
                        binding.rvPlanHoy.visibility = View.VISIBLE
                        binding.rvPlanHoy.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvPlanHoy.adapter = PlanAdapter(plan.take(3))
                    }
                }
            } catch (_: Exception) {
                if (_binding != null) binding.tvSinPlan.visibility = View.VISIBLE
            }
        }
    }

    private fun updateEstado(hasAlerta: Boolean) {
        val px10 = (10 * resources.displayMetrics.density).toInt()
        val px4 = (4 * resources.displayMetrics.density).toInt()
        if (hasAlerta) {
            binding.tvEstado.text = getString(R.string.status_riesgo)
            binding.tvEstado.setBackgroundResource(R.drawable.bg_status_warning)
            binding.tvEstado.setTextColor("#d97706".toColorInt())
        } else {
            binding.tvEstado.text = getString(R.string.status_estable)
            binding.tvEstado.setBackgroundResource(R.drawable.bg_status_ok)
            binding.tvEstado.setTextColor("#16a34a".toColorInt())
        }
        binding.tvEstado.setPadding(px10, px4, px10, px4)
    }

    override fun onResume() {
        super.onResume()
        if (_binding != null) loadData()
    }
}
