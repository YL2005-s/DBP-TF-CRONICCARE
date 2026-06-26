package com.example.croniccare.ui.activities

import android.R
import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.example.croniccare.data.models.RegistrarMetricaRequest
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityRegistrarMetricaBinding
import com.example.croniccare.utils.SessionManager
import kotlinx.coroutines.launch

class RegistrarMetricaFragment : Fragment() {

    private var _binding: ActivityRegistrarMetricaBinding? = null
    private val binding get() = _binding!!
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

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityRegistrarMetricaBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        session = SessionManager(requireContext())
        setupSpinner()
        binding.btnRegistrar.setOnClickListener { registrar() }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupSpinner() {
        val adapter = ArrayAdapter(requireContext(), R.layout.simple_spinner_item, tipoLabels)
        adapter.setDropDownViewResource(R.layout.simple_spinner_dropdown_item)
        binding.spinnerTipo.adapter = adapter

        binding.spinnerTipo.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, pos: Int, id: Long) {
                val key = tipoKeys[pos]
                binding.tvReferencia.text = referencias[key]
                binding.tilValor.hint = "${tipoLabels[pos]} (${unidades[key]})"
                binding.cardResultado.visibility = View.GONE
            }
            override fun onNothingSelected(parent: AdapterView<*>?) {}
        }

        binding.tvReferencia.text = referencias["glucosa"]
        binding.tilValor.hint = "Glucosa (mg/dL)"
    }

    private fun registrar() {
        val valorStr = binding.etValor.text?.toString()?.trim() ?: ""
        if (valorStr.isEmpty()) {
            binding.tilValor.error = getString(com.example.croniccare.R.string.error_valor_vacio)
            return
        }

        val valor = valorStr.toDoubleOrNull()
        if (valor == null) {
            binding.tilValor.error = getString(com.example.croniccare.R.string.error_valor_invalido)
            return
        }

        binding.tilValor.error = null
        setLoading(true)
        binding.cardResultado.visibility = View.GONE

        val tipoIdx = binding.spinnerTipo.selectedItemPosition
        val tipo = tipoKeys[tipoIdx]

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.registrarMetrica(
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
                showResultError(getString(com.example.croniccare.R.string.error_network))
            } finally {
                if (_binding != null) setLoading(false)
            }
        }
    }

    private fun showResult(isAlerta: Boolean, mensaje: String) {
        binding.cardResultado.visibility = View.VISIBLE
        binding.tvResultadoMsg.text = mensaje

        if (isAlerta) {
            binding.cardResultado.setCardBackgroundColor(Color.parseColor("#fee2e2"))
            binding.cardResultado.strokeColor = Color.parseColor("#fca5a5")
            binding.ivResultadoIcon.setImageResource(R.drawable.ic_dialog_alert)
            binding.ivResultadoIcon.setColorFilter(Color.parseColor("#dc2626"))
            binding.tvResultadoMsg.setTextColor(Color.parseColor("#dc2626"))
        } else {
            binding.cardResultado.setCardBackgroundColor(Color.parseColor("#dcfce7"))
            binding.cardResultado.strokeColor = Color.parseColor("#86efac")
            binding.ivResultadoIcon.setImageResource(R.drawable.ic_dialog_info)
            binding.ivResultadoIcon.setColorFilter(Color.parseColor("#16a34a"))
            binding.tvResultadoMsg.setTextColor(Color.parseColor("#16a34a"))
        }
    }

    private fun showResultError(msg: String) {
        binding.cardResultado.visibility = View.VISIBLE
        binding.cardResultado.setCardBackgroundColor(Color.parseColor("#fee2e2"))
        binding.cardResultado.strokeColor = Color.parseColor("#fca5a5")
        binding.ivResultadoIcon.setImageResource(R.drawable.ic_dialog_alert)
        binding.ivResultadoIcon.setColorFilter(Color.parseColor("#dc2626"))
        binding.tvResultadoMsg.text = msg
        binding.tvResultadoMsg.setTextColor(Color.parseColor("#dc2626"))
    }

    private fun setLoading(loading: Boolean) {
        binding.btnRegistrar.isEnabled = !loading
        binding.progressRegistrar.visibility = if (loading) View.VISIBLE else View.GONE
    }
}
