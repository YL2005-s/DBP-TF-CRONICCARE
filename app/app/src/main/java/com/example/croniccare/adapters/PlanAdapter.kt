package com.example.croniccare.adapters

import android.graphics.Color
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.example.croniccare.data.models.PlanCuidado
import com.example.croniccare.databinding.ItemPlanBinding

class PlanAdapter(private val items: List<PlanCuidado>) :
    RecyclerView.Adapter<PlanAdapter.ViewHolder>() {

    inner class ViewHolder(val binding: ItemPlanBinding) :
        RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemPlanBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val plan = items[position]
        val b = holder.binding

        b.tvDescripcion.text = plan.descripcion
        b.tvFrecuencia.text = plan.frecuenciaDisplay

        val horaParts = plan.hora.split(":")
        if (horaParts.size >= 2) {
            val hour = horaParts[0].toIntOrNull() ?: 0
            val min = horaParts[1]
            b.tvHora.text = if (hour > 12) "%02d:%s".format(hour - 12, min) else "%02d:%s".format(hour, min)
            b.tvAmPm.text = if (hour >= 12) "PM" else "AM"
        } else {
            b.tvHora.text = plan.hora
            b.tvAmPm.text = ""
        }

        if (plan.tipo == "medicamento") {
            b.tvTipo.text = "MED"
            b.tvTipo.setTextColor(Color.parseColor("#1565C0"))
            b.tvTipo.setBackgroundColor(Color.parseColor("#E3F2FD"))
        } else {
            b.tvTipo.text = "MED"
            b.tvTipo.setTextColor(Color.parseColor("#00838F"))
            b.tvTipo.setBackgroundColor(Color.parseColor("#E0F7FA"))
        }

        // Round corners on tipo chip programmatically via padding
        b.tvTipo.setPadding(20, 8, 20, 8)
    }

    override fun getItemCount() = items.size
}
