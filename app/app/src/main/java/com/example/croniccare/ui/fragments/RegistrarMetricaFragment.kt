package com.example.croniccare.ui.fragments

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.InputMethodManager
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.FrameLayout
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.example.croniccare.R
import com.example.croniccare.data.models.RegistrarMetricaRequest
import com.example.croniccare.data.network.RetrofitClient
import com.example.croniccare.databinding.ActivityRegistrarMetricaBinding
import com.example.croniccare.utils.SessionManager
import com.example.croniccare.utils.applyStatusBarTopPadding
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.google.android.material.button.MaterialButton
import kotlinx.coroutines.launch

class RegistrarMetricaFragment : Fragment() {

    private data class DialogConfig(
        val iconEmoji: String,
        val circleBg: String,
        val circleStroke: String,
        val iconColor: String,
        val title: String,
        val chipLabel: String,
        val chipBg: String,
        val chipText: String,
        val msg: String
    )

    private var _binding: ActivityRegistrarMetricaBinding? = null
    private val binding get() = _binding!!
    private lateinit var session: SessionManager

    private val tipoLabels = listOf("Glucosa", "Presión arterial", "Saturación O₂", "Frec. cardíaca")
    private val tipoKeys = listOf("glucosa", "presion", "saturacion", "frecuencia")
    private val referencias = mapOf(
        "glucosa"    to "Normal: 70–99 mg/dL | Alerta: > 126 mg/dL",
        "presion"    to "Normal: < 120/80 mmHg | Alerta: > 140 mmHg sistólica",
        "saturacion" to "Normal: ≥ 95% | Alerta: < 90%",
        "frecuencia" to "Normal: 60–100 lpm"
    )
    private val unidades = mapOf(
        "glucosa" to "mg/dL", "presion" to "mmHg", "saturacion" to "%", "frecuencia" to "lpm"
    )

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = ActivityRegistrarMetricaBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.layoutHeader.applyStatusBarTopPadding()
        session = SessionManager(requireContext())
        setupSpinner()
        binding.btnRegistrar.setOnClickListener { registrar() }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupSpinner() {
        val adapter = ArrayAdapter(requireContext(), android.R.layout.simple_spinner_item, tipoLabels)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerTipo.adapter = adapter

        binding.spinnerTipo.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, pos: Int, id: Long) {
                val key = tipoKeys[pos]
                binding.tvReferencia.text = referencias[key]
                val esPresion = key == "presion"
                binding.tilValor.hint = if (esPresion) "Sistólica (mmHg)" else "${tipoLabels[pos]} (${unidades[key]})"
                binding.tilDiastolica.visibility = if (esPresion) View.VISIBLE else View.GONE
                if (!esPresion) {
                    binding.etDiastolica.text?.clear()
                    binding.tilDiastolica.error = null
                }
            }
            override fun onNothingSelected(parent: AdapterView<*>?) {}
        }

        binding.tvReferencia.text = referencias["glucosa"]
        binding.tilValor.hint = "Glucosa (mg/dL)"
    }

    private fun registrar() {
        val valorStr = binding.etValor.text?.toString()?.trim() ?: ""
        if (valorStr.isEmpty()) { binding.tilValor.error = getString(R.string.error_valor_vacio); return }
        val valor = valorStr.toDoubleOrNull()
        if (valor == null) { binding.tilValor.error = getString(R.string.error_valor_invalido); return }
        binding.tilValor.error = null

        val tipoIdx   = binding.spinnerTipo.selectedItemPosition
        val tipo      = tipoKeys[tipoIdx]
        val tipoLabel = tipoLabels[tipoIdx]
        val unidad    = unidades[tipo] ?: ""

        var valorDiastolica: Double? = null
        if (tipo == "presion") {
            val diastolicaStr = binding.etDiastolica.text?.toString()?.trim() ?: ""
            if (diastolicaStr.isEmpty()) { binding.tilDiastolica.error = getString(R.string.error_valor_vacio); return }
            valorDiastolica = diastolicaStr.toDoubleOrNull()
            if (valorDiastolica == null) { binding.tilDiastolica.error = getString(R.string.error_valor_invalido); return }
            if (valor < 60 || valor > 250) { binding.tilValor.error = "Sistólica debe estar entre 60 y 250 mmHg"; return }
            if (valorDiastolica < 40 || valorDiastolica > 150) { binding.tilDiastolica.error = "Diastólica debe estar entre 40 y 150 mmHg"; return }
            binding.tilDiastolica.error = null
        }

        setLoading(true)

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val response = RetrofitClient.instance.registrarMetrica(
                    RegistrarMetricaRequest(tipo, valor, valorDiastolica)
                )
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    val valorDisplay = if (valorDiastolica != null)
                        "${valor.toInt()} / ${valorDiastolica.toInt()}"
                    else
                        if (valor == valor.toLong().toDouble()) valor.toLong().toString()
                        else "%.1f".format(valor)

                    binding.etValor.text?.clear()
                    binding.etDiastolica.text?.clear()

                    val config = buildConfig(result.alerta, result.criticidad)
                    showDialog(config, valorDisplay, "$tipoLabel · $unidad")
                } else {
                    showDialog(errorConfig(), "—", "")
                }
            } catch (_: Exception) {
                showDialog(errorConfig(), "—", "")
            } finally {
                if (_binding != null) setLoading(false)
            }
        }
    }

    private fun buildConfig(isAlerta: Boolean, criticidad: String?): DialogConfig = when {
        !isAlerta -> DialogConfig(
            iconEmoji    = "✓",
            circleBg     = "#dcfce7", circleStroke = "#86efac", iconColor = "#16a34a",
            title        = "¡Todo en orden!",
            chipLabel    = "Normal",    chipBg = "#dcfce7", chipText = "#16a34a",
            msg          = "Tu valor está dentro del rango normal. Sigue así."
        )
        criticidad == "critica" -> DialogConfig(
            iconEmoji    = "!",
            circleBg     = "#fee2e2", circleStroke = "#fca5a5", iconColor = "#dc2626",
            title        = "¡Alerta generada!",
            chipLabel    = "Crítico",   chipBg = "#fee2e2", chipText = "#dc2626",
            msg          = "Se ha generado una alerta para tu médico. Consulta a tu médico cuanto antes."
        )
        else -> DialogConfig(
            iconEmoji    = "!",
            circleBg     = "#fef3c7", circleStroke = "#fcd34d", iconColor = "#d97706",
            title        = "Valor elevado",
            chipLabel    = if (criticidad == "moderada") "Moderado" else "Leve",
            chipBg       = "#fef3c7", chipText = "#d97706",
            msg          = "Tu valor está fuera del rango recomendado. Monitoréalo con atención."
        )
    }

    private fun errorConfig() = DialogConfig(
        iconEmoji    = "✕",
        circleBg     = "#fee2e2", circleStroke = "#fca5a5", iconColor = "#dc2626",
        title        = "Error al registrar",
        chipLabel    = "Sin conexión", chipBg = "#fee2e2", chipText = "#dc2626",
        msg          = getString(R.string.error_network)
    )

    private fun showDialog(config: DialogConfig, valorDisplay: String, tipoLabel: String) {
        hideKeyboard()

        val dialog     = BottomSheetDialog(requireContext())
        val dialogView = layoutInflater.inflate(R.layout.dialog_resultado_metrica, null)
        dialog.setContentView(dialogView)

        val dp = resources.displayMetrics.density

        dialogView.findViewById<FrameLayout>(R.id.containerDialogIcon).background =
            GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(Color.parseColor(config.circleBg))
                setStroke((2 * dp).toInt(), Color.parseColor(config.circleStroke))
            }

        dialogView.findViewById<TextView>(R.id.tvDialogEstado).also { chip ->
            chip.background = GradientDrawable().apply {
                setColor(Color.parseColor(config.chipBg))
                setStroke((1 * dp).toInt(), Color.parseColor(config.chipText))
                cornerRadius = 99 * dp
            }
            chip.text = config.chipLabel
            chip.setTextColor(Color.parseColor(config.chipText))
        }

        dialogView.findViewById<TextView>(R.id.tvDialogIcon).also {
            it.text = config.iconEmoji
            it.setTextColor(Color.parseColor(config.iconColor))
        }
        dialogView.findViewById<TextView>(R.id.tvDialogTitle).text  = config.title
        dialogView.findViewById<TextView>(R.id.tvDialogValor).text  = valorDisplay
        dialogView.findViewById<TextView>(R.id.tvDialogTipo).text   = tipoLabel
        dialogView.findViewById<TextView>(R.id.tvDialogMsg).text    = config.msg

        dialogView.findViewById<MaterialButton>(R.id.btnDialogOk)
            .setOnClickListener { dialog.dismiss() }

        dialog.show()
    }

    private fun hideKeyboard() {
        val imm = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        activity?.currentFocus?.let { imm.hideSoftInputFromWindow(it.windowToken, 0) }
    }

    private fun setLoading(loading: Boolean) {
        binding.btnRegistrar.isEnabled = !loading
        binding.progressRegistrar.visibility = if (loading) View.VISIBLE else View.GONE
    }
}
