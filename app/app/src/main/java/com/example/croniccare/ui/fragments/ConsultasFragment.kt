package com.example.croniccare.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.ui.adapters.ConsultaAdapter
import com.example.croniccare.data.network.ApiResult
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.data.network.safeApiCall
import com.example.croniccare.databinding.ActivityConsultasBinding
import com.example.croniccare.utils.ScreenStateManager
import com.example.croniccare.utils.applyStatusBarTopPadding
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class ConsultasFragment : Fragment() {

    private var _binding: ActivityConsultasBinding? = null
    private val binding get() = _binding!!
    private var stateManager: ScreenStateManager? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityConsultasBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.layoutHeader.applyStatusBarTopPadding()
        stateManager = ScreenStateManager(
            skeleton = binding.skeletonList.root,
            content  = binding.rvConsultas,
            empty    = binding.layoutEmpty
        )
        loadConsultas()
    }

    override fun onDestroyView() {
        stateManager?.destroy()
        stateManager = null
        super.onDestroyView()
        _binding = null
    }

    private fun loadConsultas() {
        binding.bannerProximaCita.visibility = View.GONE
        stateManager?.showLoading()

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMisConsultas() }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val consultas = result.data
                    showProximaCita(consultas.mapNotNull { it.proximaCita })
                    if (consultas.isEmpty()) {
                        stateManager?.showEmpty()
                    } else {
                        binding.rvConsultas.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvConsultas.adapter = ConsultaAdapter(consultas)
                        stateManager?.showContent()
                    }
                }
                is ApiResult.Error -> stateManager?.showEmpty()
            }
        }
    }

    private fun showProximaCita(fechas: List<String>) {
        val hoy = Calendar.getInstance().time
        val inputFmt = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val proxima = fechas.filter {
            try { inputFmt.parse(it)?.after(hoy) == true } catch (_: Exception) { false }
        }.minOrNull() ?: return

        val outFmt = SimpleDateFormat("EEE d 'de' MMM · yyyy", Locale("es"))
        binding.tvProximaCitaBanner.text = try {
            outFmt.format(inputFmt.parse(proxima)!!)
        } catch (_: Exception) { proxima }
        binding.bannerProximaCita.visibility = View.VISIBLE
    }
}
