package com.example.croniccare.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.ui.adapters.MetricaAdapter
import com.example.croniccare.ui.adapters.PlanAdapter
import com.example.croniccare.data.network.ApiResult
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.data.network.safeApiCall
import com.example.croniccare.databinding.ActivityDashboardBinding
import com.example.croniccare.utils.ScreenStateManager
import com.example.croniccare.utils.SessionManager
import com.example.croniccare.utils.applyStatusBarTopPadding
import kotlinx.coroutines.launch
import androidx.core.graphics.toColorInt
import com.example.croniccare.MainActivity
import com.example.croniccare.R

class DashboardFragment : Fragment() {

    private var _binding: ActivityDashboardBinding? = null
    private val binding get() = _binding!!
    private lateinit var session: SessionManager
    private var metricasManager: ScreenStateManager? = null
    private var planManager: ScreenStateManager? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.layoutHeader.applyStatusBarTopPadding()
        session = SessionManager(requireContext())
        setupHeader()
        setupListeners()

        metricasManager = ScreenStateManager(
            skeleton = binding.skeletonMetricas.root,
            content = binding.rvMetricasRecientes,
            empty = binding.tvSinMetricas
        )
        planManager = ScreenStateManager(
            skeleton = binding.skeletonPlan.root,
            content = binding.rvPlanHoy,
            empty = binding.tvSinPlan
        )

        loadData()
    }

    override fun onDestroyView() {
        metricasManager?.destroy()
        planManager?.destroy()
        metricasManager = null
        planManager = null
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
        binding.btnVerHistorial.setOnClickListener { findNavController().navigate(R.id.nav_historial) }
        binding.bannerAlertasCriticas.setOnClickListener { findNavController().navigate(R.id.nav_alertas) }
        binding.btnVerPlan.setOnClickListener { findNavController().navigate(R.id.nav_plan) }
        binding.cardAccesoAlertas.setOnClickListener { findNavController().navigate(R.id.nav_alertas) }
        binding.cardAccesoMedicamentos.setOnClickListener { findNavController().navigate(R.id.nav_prescripciones) }
        binding.cardAccesoConsultas.setOnClickListener { findNavController().navigate(R.id.nav_consultas) }
    }

    private fun loadData() {
        metricasManager?.showLoading()
        planManager?.showLoading()
        binding.bannerAlertasCriticas.visibility = View.GONE

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMisMetricas() }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val recientes = result.data.take(3)
                    if (recientes.isEmpty()) {
                        metricasManager?.showEmpty()
                    } else {
                        binding.rvMetricasRecientes.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvMetricasRecientes.adapter = MetricaAdapter(recientes)
                        metricasManager?.showContent()
                    }
                }
                is ApiResult.Error -> metricasManager?.showEmpty()
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMiPlan() }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val plan = result.data
                    if (plan.isEmpty()) {
                        planManager?.showEmpty()
                        binding.tvResumenPlan.visibility = View.GONE
                    } else {
                        binding.rvPlanHoy.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvPlanHoy.adapter = PlanAdapter(plan.take(3))
                        planManager?.showContent()
                        binding.tvResumenPlan.text = "Hoy: ${plan.size} tareas"
                        binding.tvResumenPlan.visibility = View.VISIBLE
                    }
                }
                is ApiResult.Error -> planManager?.showEmpty()
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMisAlertas() }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val tieneCriticas = result.data.any { it.criticidad == "critica" }
                    updateEstado(tieneCriticas)
                    binding.bannerAlertasCriticas.visibility = if (tieneCriticas) View.VISIBLE else View.GONE
                }
                is ApiResult.Error -> binding.bannerAlertasCriticas.visibility = View.GONE
            }
        }
    }

    private fun updateEstado(hasAlerta: Boolean) {
        val px10 = (10 * resources.displayMetrics.density).toInt()
        val px4  = (4  * resources.displayMetrics.density).toInt()
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
