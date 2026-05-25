package com.example.croniccare

import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.example.croniccare.data.models.RegistrarMetricaRequest
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityRegistrarMetricaBinding
import com.example.croniccare.utils.SessionManager
import kotlinx.coroutines.launch

class RegistrarMetricaActivity : AppCompatActivity() {

    private lateinit var binding: ActivityRegistrarMetricaBinding
    private lateinit var session: SessionManager

    private val tipoLabels = listOf("Glucosa", "Presión arterial", "Saturación O₂", "Frec. cardíaca")
    private val tipoKeys = listOf("glucosa", "presion", "saturacion", "frecuencia")
    private val referencias = mapOf(
        "glucosa" to "Normal: 70–99 mg/dL | Alerta: > 126 mg/dL",
        "presion" to "Normal: < 120/80 mmHg | Alerta: > 140 mmHg sistólica",
        "saturacion" to "Normal: ≥ 95% | Alerta: < 90%",
        "frecuencia" to "Normal: 60–100 lpm"
    )
    private val unidades = mapOf(
        "glucosa" to "mg/dL",
        "presion" to "mmHg",
        "saturacion" to "%",
        "frecuencia" to "lpm"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityRegistrarMetricaBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        binding.btnBack.setOnClickListener { finish() }

        setupSpinner()
        binding.btnRegistrar.setOnClickListener { registrar() }
    }

    private fun setupSpinner() {
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, tipoLabels)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerTipo.adapter = adapter

        binding.spinnerTipo.onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: android.view.View?, pos: Int, id: Long) {
                val key = tipoKeys[pos]
                binding.tvReferencia.text = referencias[key]
                binding.tilValor.hint = "${tipoLabels[pos]} (${unidades[key]})"
                binding.cardResultado.visibility = View.GONE
            }
            override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
        }

        // Trigger initial reference
        binding.tvReferencia.text = referencias["glucosa"]
        binding.tilValor.hint = "Glucosa (mg/dL)"
    }

    private fun registrar() {
        val valorStr = binding.etValor.text?.toString()?.trim() ?: ""
        if (valorStr.isEmpty()) {
            binding.tilValor.error = getString(R.string.error_valor_vacio)
            return
        }

        val valor = valorStr.toDoubleOrNull()
        if (valor == null) {
            binding.tilValor.error = getString(R.string.error_valor_invalido)
            return
        }

        binding.tilValor.error = null
        setLoading(true)
        binding.cardResultado.visibility = View.GONE

        val tipoIdx = binding.spinnerTipo.selectedItemPosition
        val tipo = tipoKeys[tipoIdx]

        lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.registrarMetrica(
                    session.getAuthToken(),
                    RegistrarMetricaRequest(tipo, valor)
                )
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    showResult(result.alerta, result.mensaje)
                    binding.etValor.text?.clear()
                } else {
                    showResultError("No se pudo registrar. Intenta de nuevo.")
                }
            } catch (e: Exception) {
                showResultError(getString(R.string.error_network))
            } finally {
                setLoading(false)
            }
        }
    }

    private fun showResult(isAlerta: Boolean, mensaje: String) {
        binding.cardResultado.visibility = View.VISIBLE
        binding.tvResultadoMsg.text = mensaje

        if (isAlerta) {
            binding.cardResultado.setCardBackgroundColor(Color.parseColor("#FFEBEE"))
            binding.ivResultadoIcon.setImageResource(android.R.drawable.ic_dialog_alert)
            binding.ivResultadoIcon.setColorFilter(Color.parseColor("#C62828"))
            binding.tvResultadoMsg.setTextColor(Color.parseColor("#C62828"))
        } else {
            binding.cardResultado.setCardBackgroundColor(Color.parseColor("#E8F5E9"))
            binding.ivResultadoIcon.setImageResource(android.R.drawable.ic_dialog_info)
            binding.ivResultadoIcon.setColorFilter(Color.parseColor("#2E7D32"))
            binding.tvResultadoMsg.setTextColor(Color.parseColor("#2E7D32"))
        }
    }

    private fun showResultError(msg: String) {
        binding.cardResultado.visibility = View.VISIBLE
        binding.cardResultado.setCardBackgroundColor(Color.parseColor("#FFEBEE"))
        binding.ivResultadoIcon.setImageResource(android.R.drawable.ic_dialog_alert)
        binding.ivResultadoIcon.setColorFilter(Color.parseColor("#C62828"))
        binding.tvResultadoMsg.text = msg
        binding.tvResultadoMsg.setTextColor(Color.parseColor("#C62828"))
    }

    private fun setLoading(loading: Boolean) {
        binding.btnRegistrar.isEnabled = !loading
        binding.progressRegistrar.visibility = if (loading) View.VISIBLE else View.GONE
    }
}
