package com.example.croniccare.ui.activities

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.adapters.PlanAdapter
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityPlanCuidadoBinding
import kotlinx.coroutines.launch

class PlanCuidadoFragment : Fragment() {

    private var _binding: ActivityPlanCuidadoBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityPlanCuidadoBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        loadPlan()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun loadPlan() {
        binding.progressPlan.visibility = View.VISIBLE
        binding.rvPlan.visibility = View.GONE
        binding.layoutEmpty.visibility = View.GONE

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.getMiPlan()
                if (response.isSuccessful) {
                    val plan = response.body() ?: emptyList()
                    binding.progressPlan.visibility = View.GONE

                    if (plan.isEmpty()) {
                        binding.layoutEmpty.visibility = View.VISIBLE
                    } else {
                        binding.rvPlan.visibility = View.VISIBLE
                        binding.rvPlan.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvPlan.adapter = PlanAdapter(plan)
                    }
                } else {
                    showEmpty()
                }
            } catch (e: Exception) {
                showEmpty()
            }
        }
    }

    private fun showEmpty() {
        if (_binding == null) return
        binding.progressPlan.visibility = View.GONE
        binding.layoutEmpty.visibility = View.VISIBLE
    }
}
