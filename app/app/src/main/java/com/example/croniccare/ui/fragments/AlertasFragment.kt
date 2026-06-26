package com.example.croniccare.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.ui.adapters.AlertaAdapter
import com.example.croniccare.data.network.ApiResult
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.data.network.safeApiCall
import com.example.croniccare.databinding.ActivityAlertasBinding
import com.example.croniccare.utils.ScreenStateManager
import com.example.croniccare.utils.applyStatusBarTopPadding
import com.google.android.material.tabs.TabLayout
import kotlinx.coroutines.launch

class AlertasFragment : Fragment() {

    private var _binding: ActivityAlertasBinding? = null
    private val binding get() = _binding!!
    private var stateManager: ScreenStateManager? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityAlertasBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.layoutHeader.applyStatusBarTopPadding()
        stateManager = ScreenStateManager(
            skeleton = binding.skeletonList.root,
            content = binding.rvAlertas,
            empty = binding.layoutEmpty
        )
        setupTabs()
        loadAlertas(resuelta = false)
    }

    override fun onDestroyView() {
        stateManager?.destroy()
        stateManager = null
        super.onDestroyView()
        _binding = null
    }

    private fun setupTabs() {
        binding.tabAlertas.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) = loadAlertas(tab.position == 1)
            override fun onTabUnselected(tab: TabLayout.Tab) {}
            override fun onTabReselected(tab: TabLayout.Tab) {}
        })
    }

    private fun loadAlertas(resuelta: Boolean) {
        if (_binding == null) return
        stateManager?.showLoading()

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMisAlertas(resuelta) }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val alertas = result.data
                    binding.tvSubtitleAlertas.text = "${alertas.size} alerta${if (alertas.size != 1) "s" else ""}"
                    if (alertas.isEmpty()) {
                        binding.tvEmptyMsg.text = if (resuelta) "Sin alertas resueltas" else "Sin alertas pendientes · Sigue así"
                        stateManager?.showEmpty()
                    } else {
                        binding.rvAlertas.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvAlertas.adapter = AlertaAdapter(alertas)
                        stateManager?.showContent()
                    }
                }
                is ApiResult.Error -> {
                    if (_binding == null) return@launch
                    binding.tvEmptyMsg.text = if (resuelta) "Sin alertas resueltas" else "Sin alertas pendientes · Sigue así"
                    stateManager?.showEmpty()
                }
            }
        }
    }
}
