package com.example.croniccare.ui.fragments

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.ui.adapters.PlanAdapter
import com.example.croniccare.data.network.ApiResult
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.data.network.safeApiCall
import com.example.croniccare.databinding.ActivityPlanCuidadoBinding
import com.example.croniccare.utils.ScreenStateManager
import com.example.croniccare.utils.applyStatusBarTopPadding
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class PlanCuidadoFragment : Fragment() {

    private var _binding: ActivityPlanCuidadoBinding? = null
    private val binding get() = _binding!!
    private val hoy get() = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
    private var stateManager: ScreenStateManager? = null

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityPlanCuidadoBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.layoutHeader.applyStatusBarTopPadding()
        stateManager = ScreenStateManager(
            skeleton = binding.skeletonList.root,
            content = binding.rvPlan,
            empty = binding.layoutEmpty
        )
        loadPlan()
    }

    override fun onDestroyView() {
        stateManager?.destroy()
        stateManager = null
        super.onDestroyView()
        _binding = null
    }

    private fun loadPlan() {
        stateManager?.showLoading()
        binding.cardProgreso.visibility = View.GONE

        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = safeApiCall { RetrofitClient.instance.getMiPlan() }) {
                is ApiResult.Success -> {
                    if (_binding == null) return@launch
                    val plan = result.data
                    if (plan.isEmpty()) {
                        stateManager?.showEmpty()
                    } else {
                        val completedIds = loadCompletedIds(plan.map { it.id })
                        updateProgress(completedIds.size, plan.size)
                        binding.cardProgreso.visibility = View.VISIBLE
                        stateManager?.showContent()
                        binding.rvPlan.layoutManager = LinearLayoutManager(requireContext())
                        binding.rvPlan.adapter = PlanAdapter(
                            items = plan,
                            completedIds = completedIds,
                            onToggle = { planId, done ->
                                saveCompletion(planId, done)
                                val cnt = completedIds.size
                                updateProgress(cnt, plan.size)
                            }
                        )
                    }
                }
                is ApiResult.Error -> stateManager?.showEmpty()
            }
        }
    }

    private fun updateProgress(done: Int, total: Int) {
        if (_binding == null) return
        binding.tvProgreso.text = "$done de $total"
        binding.progressBarDia.max = total
        binding.progressBarDia.progress = done
    }

    private fun prefKey(planId: Int) = "cumplimiento_${planId}_$hoy"

    private fun loadCompletedIds(allIds: List<Int>): MutableSet<Int> {
        val prefs = requireContext().getSharedPreferences("plan_adherencia", Context.MODE_PRIVATE)
        return allIds.filter { prefs.getBoolean(prefKey(it), false) }.toMutableSet()
    }

    private fun saveCompletion(planId: Int, done: Boolean) {
        requireContext()
            .getSharedPreferences("plan_adherencia", Context.MODE_PRIVATE)
            .edit()
            .putBoolean(prefKey(planId), done)
            .apply()
    }
}
