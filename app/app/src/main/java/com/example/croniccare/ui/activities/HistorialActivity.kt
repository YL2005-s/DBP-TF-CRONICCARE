package com.example.croniccare.ui.activities

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.adapters.MetricaAdapter
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityHistorialBinding
import kotlinx.coroutines.launch

class HistorialFragment : Fragment() {

    private var _binding: ActivityHistorialBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityHistorialBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        loadHistorial()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun loadHistorial() {
        binding.progressHistorial.visibility = View.VISIBLE
        binding.rvHistorial.visibility = View.GONE
        binding.layoutEmpty.visibility = View.GONE

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.getMisMetricas()
                if (response.isSuccessful) {
                    val metricas = response.body() ?: emptyList()
                    binding.progressHistorial.visibility = View.GONE

                    if (metricas.isEmpty()) {
                        binding.layoutEmpty.visibility = View.VISIBLE
                    } else {
                        binding.rvHistorial.visibility = View.VISIBLE
                        binding.rvHistorial.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvHistorial.adapter = MetricaAdapter(metricas)
                    }
                } else {
                    showEmpty()
                }
            } catch (_: Exception) {
                showEmpty()
            }
        }
    }

    private fun showEmpty() {
        if (_binding == null) return
        binding.progressHistorial.visibility = View.GONE
        binding.layoutEmpty.visibility = View.VISIBLE
    }
}
