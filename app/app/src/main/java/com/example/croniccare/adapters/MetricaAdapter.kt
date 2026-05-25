package com.example.croniccare.adapters

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.example.croniccare.data.models.Metrica
import com.example.croniccare.databinding.ItemMetricaBinding
import java.text.SimpleDateFormat
import java.util.*

class MetricaAdapter(private val items: List<Metrica>) :
    RecyclerView.Adapter<MetricaAdapter.ViewHolder>() {

    inner class ViewHolder(val binding: ItemMetricaBinding) :
        RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemMetricaBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val metrica = items[position]
        val b = holder.binding

        b.tvTipo.text = tipoLabel(metrica.tipo)
        b.tvTipoIcon.text = tipoEmoji(metrica.tipo)
        b.tvValor.text = formatValor(metrica.valor)
        b.tvUnidad.text = unidad(metrica.tipo)
        b.tvFecha.text = formatFecha(metrica.fecha)

        if (metrica.alerta) {
            b.viewIndicator.setBackgroundColor(Color.parseColor("#C62828"))
            b.tvAlerta.visibility = View.VISIBLE
            b.tvAlerta.text = "ALERTA"
            b.tvAlerta.setTextColor(Color.parseColor("#C62828"))
            b.tvAlerta.setBackgroundColor(Color.parseColor("#FFEBEE"))
            b.tvValor.setTextColor(Color.parseColor("#C62828"))
            b.layoutIconBg.setBackgroundColor(Color.parseColor("#FFEBEE"))
        } else {
            b.viewIndicator.setBackgroundColor(Color.parseColor("#1565C0"))
            b.tvAlerta.visibility = View.GONE
            b.tvValor.setTextColor(Color.parseColor("#1A237E"))
            b.layoutIconBg.setBackgroundColor(Color.parseColor("#E3F2FD"))
        }
    }

    override fun getItemCount() = items.size

    private fun tipoLabel(tipo: String) = when (tipo) {
        "glucosa" -> "Glucosa"
        "presion" -> "Presión arterial"
        "saturacion" -> "Saturación O₂"
        "frecuencia" -> "Frec. cardíaca"
        else -> tipo
    }

    private fun tipoEmoji(tipo: String) = when (tipo) {
        "glucosa" -> "🩸"
        "presion" -> "💓"
        "saturacion" -> "🫁"
        "frecuencia" -> "❤️"
        else -> "📊"
    }

    private fun unidad(tipo: String) = when (tipo) {
        "glucosa" -> "mg/dL"
        "presion" -> "mmHg"
        "saturacion" -> "%"
        "frecuencia" -> "lpm"
        else -> ""
    }

    private fun formatValor(valor: Double): String {
        return if (valor == valor.toLong().toDouble()) valor.toLong().toString()
        else "%.1f".format(valor)
    }

    private fun formatFecha(fecha: String): String {
        return try {
            val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS", Locale.getDefault())
            val outputFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
            val date = inputFormat.parse(fecha) ?: return fecha
            outputFormat.format(date)
        } catch (e: Exception) {
            try {
                val inputFormat2 = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
                val outputFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
                val date = inputFormat2.parse(fecha) ?: return fecha
                outputFormat.format(date)
            } catch (e2: Exception) {
                fecha
            }
        }
    }
}
