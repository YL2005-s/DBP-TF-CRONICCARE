package com.example.croniccare.ui.adapters

import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.example.croniccare.data.models.Consulta
import com.example.croniccare.databinding.ItemConsultaBinding
import java.text.SimpleDateFormat
import java.util.*

class ConsultaAdapter(private val items: List<Consulta>) :
    RecyclerView.Adapter<ConsultaAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemConsultaBinding) :
        RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemConsultaBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val consulta = items[position]
        val b = holder.binding

        b.tvTipo.text = consulta.tipoDisplay
        b.tvFecha.text = formatFechaHora(consulta.fechaHora)
        b.tvMedico.text = consulta.medicoNombre ?: ""
        setEstadoChip(b.tvEstado, consulta.estado, consulta.estadoDisplay)

        if (consulta.diagnostico.isNotBlank()) {
            b.tvDiagnostico.text = consulta.diagnostico
            b.tvDiagnostico.visibility = View.VISIBLE
        } else {
            b.tvDiagnostico.visibility = View.GONE
        }

        if (!consulta.proximaCita.isNullOrBlank()) {
            b.tvProximaCita.text = formatFechaCita(consulta.proximaCita)
            b.layoutProximaCita.visibility = View.VISIBLE
        } else {
            b.layoutProximaCita.visibility = View.GONE
        }
    }

    override fun getItemCount() = items.size

    private fun setEstadoChip(tv: TextView, estado: String, label: String) {
        val (bgHex, textHex) = when (estado) {
            "programada" -> "#dbeafe" to "#1e40af"
            "realizada" -> "#dcfce7" to "#16a34a"
            "cancelada" -> "#fee2e2" to "#dc2626"
            "no_asistio" -> "#fef3c7" to "#d97706"
            else -> "#f1f5f9" to "#475569"
        }
        tv.text = label.uppercase()
        tv.setTextColor(Color.parseColor(textHex))
        val dp6 = (6 * tv.resources.displayMetrics.density)
        tv.background = GradientDrawable().apply {
            setColor(Color.parseColor(bgHex))
            cornerRadius = dp6
        }
    }

    private fun formatFechaHora(fechaHora: String): String {
        return try {
            val clean = fechaHora.replace(Regex("\\.\\d+"), "")
            val input = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.getDefault())
            val output = SimpleDateFormat("dd/MM/yyyy · HH:mm", Locale.getDefault())
            output.timeZone = TimeZone.getTimeZone("America/Lima")
            output.format(input.parse(clean) ?: return fechaHora)
        } catch (_: Exception) { fechaHora }
    }

    private fun formatFechaCita(fecha: String): String {
        return try {
            val input  = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            val output = SimpleDateFormat("EEE d MMM · yyyy", Locale("es"))
            output.format(input.parse(fecha) ?: return fecha)
        } catch (_: Exception) { fecha }
    }
}
