package com.example.croniccare.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.ui.adapters.MetricaAdapter
import com.example.croniccare.data.network.ApiResult
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.data.network.safeApiCall
import com.example.croniccare.databinding.ActivityHistorialBinding
import com.example.croniccare.utils.ScreenStateManager
import com.example.croniccare.utils.applyStatusBarTopPadding
import kotlinx.coroutines.launch

class HistorialFragment : Fragment() {

    private var _binding: ActivityHistorialBinding? = null
    private val binding get() = _binding!!
    private var stateManager: ScreenStateManager? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityHistorialBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.layoutHeader.applyStatusBarTopPadding()
        stateManager = ScreenStateManager(
            skeleton = binding.skeletonList.root,
            content  = binding.rvHistorial,
            empty    = binding.layoutEmpty
        )
        loadHistorial()
    }

    override fun onDestroyView() {
        stateManager?.destroy()
        stateManager = null
        super.onDestroyView()
        _binding = null
    }

    private fun loadHistorial() {
        stateManager?.showLoading()

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMisMetricas() }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val metricas = result.data
                    if (metricas.isEmpty()) {
                        stateManager?.showEmpty()
                    } else {
                        binding.rvHistorial.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvHistorial.adapter = MetricaAdapter(metricas)
                        stateManager?.showContent()
                    }
                }
                is ApiResult.Error -> stateManager?.showEmpty()
            }
        }
    }
}
