package com.example.croniccare.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.ui.adapters.PrescripcionAdapter
import com.example.croniccare.data.network.ApiResult
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.data.network.safeApiCall
import com.example.croniccare.databinding.ActivityPrescripcionesBinding
import com.example.croniccare.utils.ScreenStateManager
import com.example.croniccare.utils.applyStatusBarTopPadding
import com.google.android.material.tabs.TabLayout
import kotlinx.coroutines.launch

class PrescripcionesFragment : Fragment() {

    private var _binding: ActivityPrescripcionesBinding? = null
    private val binding get() = _binding!!
    private var stateManager: ScreenStateManager? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityPrescripcionesBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.layoutHeader.applyStatusBarTopPadding()
        stateManager = ScreenStateManager(
            skeleton = binding.skeletonList.root,
            content = binding.rvPrescripciones,
            empty = binding.layoutEmpty
        )
        setupTabs()
        loadPrescripciones(activa = true)
    }

    override fun onDestroyView() {
        stateManager?.destroy()
        stateManager = null
        super.onDestroyView()
        _binding = null
    }

    private fun setupTabs() {
        binding.tabPrescripciones.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) = loadPrescripciones(tab.position == 0)
            override fun onTabUnselected(tab: TabLayout.Tab) {}
            override fun onTabReselected(tab: TabLayout.Tab) {}
        })
    }

    private fun loadPrescripciones(activa: Boolean) {
        if (_binding == null) return
        stateManager?.showLoading()

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMisPrescripciones(activa) }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val lista = result.data
                    if (lista.isEmpty()) {
                        stateManager?.showEmpty()
                    } else {
                        binding.rvPrescripciones.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvPrescripciones.adapter = PrescripcionAdapter(lista)
                        stateManager?.showContent()
                    }
                }
                is ApiResult.Error -> stateManager?.showEmpty()
            }
        }
    }
}
