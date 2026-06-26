package com.example.croniccare.adapters

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.example.croniccare.R
import com.example.croniccare.data.models.Metrica
import com.example.croniccare.databinding.ItemMetricaBinding
import java.text.SimpleDateFormat
import java.util.*
import java.util.TimeZone

class MetricaAdapter(private val items: List<Metrica>) :
    RecyclerView.Adapter<MetricaAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemMetricaBinding) :
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
        b.tvValor.text = formatValorMetrica(metrica)
        b.tvUnidad.text = unidad(metrica.tipo)
        b.tvFecha.text = formatFecha(metrica.fecha)

        if (metrica.alerta) {
            b.viewIndicator.setBackgroundColor(Color.parseColor("#dc2626"))
            b.tvAlerta.visibility = View.VISIBLE
            b.tvAlerta.setBackgroundResource(R.drawable.bg_alert_badge)
            b.tvAlerta.setTextColor(Color.parseColor("#dc2626"))
            b.tvValor.setTextColor(Color.parseColor("#dc2626"))
            b.layoutIconBg.setBackgroundColor(Color.parseColor("#fee2e2"))
        } else {
            b.viewIndicator.setBackgroundColor(Color.parseColor("#1e40af"))
            b.tvAlerta.visibility = View.GONE
            b.tvValor.setTextColor(Color.parseColor("#0f172a"))
            b.layoutIconBg.setBackgroundColor(Color.parseColor("#eff6ff"))
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

    private fun formatValorMetrica(metrica: Metrica): String {
        return if (metrica.tipo == "presion" && metrica.valorDiastolica != null) {
            "${metrica.valor.toLong()}/${metrica.valorDiastolica.toLong()}"
        } else {
            val v = metrica.valor
            if (v == v.toLong().toDouble()) v.toLong().toString() else "%.1f".format(v)
        }
    }

    private fun formatFecha(fecha: String): String {
        return try {
            // Strip fractional seconds (Django returns microseconds, SimpleDateFormat can't handle them)
            val normalizada = fecha.replace(Regex("\\.\\d+"), "")
            val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
            inputFormat.timeZone = TimeZone.getTimeZone("UTC")
            val outputFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
            val date = inputFormat.parse(normalizada) ?: return fecha
            outputFormat.format(date)
        } catch (e: Exception) {
            fecha
        }
    }
}
