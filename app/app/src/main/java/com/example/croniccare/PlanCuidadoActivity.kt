package com.example.croniccare

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.adapters.PlanAdapter
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityPlanCuidadoBinding
import com.example.croniccare.utils.SessionManager
import kotlinx.coroutines.launch

class PlanCuidadoActivity : AppCompatActivity() {

    private lateinit var binding: ActivityPlanCuidadoBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPlanCuidadoBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        binding.btnBack.setOnClickListener { finish() }

        loadPlan()
    }

    private fun loadPlan() {
        binding.progressPlan.visibility = View.VISIBLE
        binding.rvPlan.visibility = View.GONE
        binding.layoutEmpty.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.getMiPlan(session.getAuthToken())
                if (response.isSuccessful) {
                    val plan = response.body() ?: emptyList()
                    binding.progressPlan.visibility = View.GONE

                    if (plan.isEmpty()) {
                        binding.layoutEmpty.visibility = View.VISIBLE
                    } else {
                        binding.rvPlan.visibility = View.VISIBLE
                        binding.rvPlan.layoutManager = LinearLayoutManager(this@PlanCuidadoActivity)
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
        binding.progressPlan.visibility = View.GONE
        binding.layoutEmpty.visibility = View.VISIBLE
    }
}
