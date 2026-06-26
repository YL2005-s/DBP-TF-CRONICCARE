package com.example.croniccare.ui.adapters

import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.example.croniccare.data.models.Prescripcion
import com.example.croniccare.databinding.ItemPrescripcionBinding
import com.example.croniccare.utils.AppColors
import java.util.Calendar

class PrescripcionAdapter(private val items: List<Prescripcion>) :
    RecyclerView.Adapter<PrescripcionAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemPrescripcionBinding) :
        RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemPrescripcionBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val prescripcion = items[position]
        val b = holder.binding

        b.tvMedicamento.text = prescripcion.medicamento
        b.tvDosis.text = prescripcion.dosis
        b.tvFrecuencia.text = prescripcion.frecuenciaDisplay
        setViaChip(b.tvVia, prescripcion.viaDisplay, prescripcion.via)

        val proximaDosis = calcProximaDosis(prescripcion.frecuencia)
        if (proximaDosis != null && prescripcion.activa) {
            b.tvProximaDosis.text = proximaDosis
            b.layoutProximaDosis.visibility = View.VISIBLE
        } else {
            b.layoutProximaDosis.visibility = View.GONE
        }

        if (prescripcion.indicaciones.isNotBlank()) {
            b.tvIndicaciones.text = prescripcion.indicaciones
            b.tvIndicaciones.visibility = View.VISIBLE
        } else {
            b.tvIndicaciones.visibility = View.GONE
        }
    }

    override fun getItemCount() = items.size

    private fun calcProximaDosis(frecuencia: String): String? {
        val intervalHours = when (frecuencia) {
            "cada_4h" -> 4
            "cada_6h" -> 6
            "cada_8h" -> 8
            "cada_12h" -> 12
            "cada_24h" -> 24
            else -> return null
        }

        val cal = Calendar.getInstance()
        val nowMins = cal.get(Calendar.HOUR_OF_DAY) * 60 + cal.get(Calendar.MINUTE)

        val anchorMins = if (intervalHours == 24) 8 * 60 else 0
        val intervalMins = intervalHours * 60

        val doseTimes = if (intervalHours == 24) {
            listOf(anchorMins)
        } else {
            generateSequence(anchorMins) { it + intervalMins }.takeWhile { it < 24 * 60 }.toList()
        }

        val nextMins = doseTimes.firstOrNull { it > nowMins }
        return if (nextMins != null) {
            "Próxima dosis: %02d:%02d".format(nextMins / 60, nextMins % 60)
        } else {
            val first = doseTimes.first()
            "Próxima dosis: mañana %02d:%02d".format(first / 60, first % 60)
        }
    }

    private fun setViaChip(tv: TextView, label: String, via: String) {
        val (bgHex, textHex) = when (via) {
            "oral"     -> AppColors.Via.oral
            "inhalada" -> AppColors.Via.inhalada
            "iv"       -> AppColors.Via.iv
            "sc"       -> AppColors.Via.sc
            "im"       -> AppColors.Via.im
            else       -> AppColors.Via.default
        }
        tv.text = label.uppercase()
        tv.setTextColor(Color.parseColor(textHex))
        val dp6 = (6 * tv.resources.displayMetrics.density)
        tv.background = GradientDrawable().apply {
            setColor(Color.parseColor(bgHex))
            cornerRadius = dp6
        }
    }
}
