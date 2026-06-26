package com.example.croniccare.ui.adapters

import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.example.croniccare.data.models.Alerta
import com.example.croniccare.databinding.ItemAlertaBinding
import com.example.croniccare.utils.AppColors
import java.text.SimpleDateFormat
import java.util.*

class AlertaAdapter(private val items: List<Alerta>) :
    RecyclerView.Adapter<AlertaAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemAlertaBinding) :
        RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemAlertaBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val alerta = items[position]
        val b = holder.binding

        val (stripeColor, bgColor, textColor, label) = criticidadColors(alerta.criticidad)
        b.viewIndicador.setBackgroundColor(Color.parseColor(stripeColor))
        setChip(b.tvCriticidad, label, bgColor, textColor)
        b.tvMensaje.text = alerta.mensaje
        b.tvFecha.text = formatFecha(alerta.fecha)
    }

    override fun getItemCount() = items.size

    private fun criticidadColors(c: String) = when (c) {
        "critica" -> listOf(AppColors.Critical.text, AppColors.Critical.bg, AppColors.Critical.text, "CRÍTICA")
        "moderada" -> listOf(AppColors.Warning.text, AppColors.Warning.bg, AppColors.Warning.text, "MODERADA")
        else -> listOf(AppColors.Leve.text, AppColors.Leve.bg, AppColors.Leve.text, "LEVE")
    }

    private fun setChip(tv: TextView, text: String, bgHex: String, textHex: String) {
        tv.text = text
        tv.setTextColor(Color.parseColor(textHex))
        val dp6 = (6 * tv.resources.displayMetrics.density)
        val bg = GradientDrawable().apply {
            setColor(Color.parseColor(bgHex))
            cornerRadius = dp6
        }
        tv.background = bg
    }

    private fun formatFecha(fecha: String): String {
        return try {
            val clean = fecha.replace(Regex("\\.\\d+"), "")
            val input = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.getDefault())
            val output = SimpleDateFormat("dd/MM/yy HH:mm", Locale.getDefault())
            output.timeZone = TimeZone.getTimeZone("America/Lima")
            output.format(input.parse(clean) ?: return fecha)
        } catch (_: Exception) { fecha }
    }
}
