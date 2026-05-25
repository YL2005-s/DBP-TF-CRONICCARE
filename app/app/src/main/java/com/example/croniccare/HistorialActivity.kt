package com.example.croniccare

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.croniccare.adapters.MetricaAdapter
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityHistorialBinding
import com.example.croniccare.utils.SessionManager
import kotlinx.coroutines.launch

class HistorialActivity : AppCompatActivity() {

    private lateinit var binding: ActivityHistorialBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHistorialBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        binding.btnBack.setOnClickListener { finish() }

        loadHistorial()
    }

    private fun loadHistorial() {
        binding.progressHistorial.visibility = View.VISIBLE
        binding.rvHistorial.visibility = View.GONE
        binding.layoutEmpty.visibility = View.GONE

        lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.getMisMetricas(session.getAuthToken())
                if (response.isSuccessful) {
                    val metricas = response.body() ?: emptyList()
                    binding.progressHistorial.visibility = View.GONE

                    if (metricas.isEmpty()) {
                        binding.layoutEmpty.visibility = View.VISIBLE
                    } else {
                        binding.rvHistorial.visibility = View.VISIBLE
                        binding.rvHistorial.layoutManager = LinearLayoutManager(this@HistorialActivity)
                        binding.rvHistorial.adapter = MetricaAdapter(metricas)
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
        binding.progressHistorial.visibility = View.GONE
        binding.layoutEmpty.visibility = View.VISIBLE
    }
}
