package com.example.croniccare.ui.adapters

import android.graphics.Color
import android.graphics.Paint
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.graphics.toColorInt
import androidx.recyclerview.widget.RecyclerView
import com.example.croniccare.R
import com.example.croniccare.data.models.PlanCuidado
import com.example.croniccare.databinding.ItemPlanBinding
import com.google.android.material.card.MaterialCardView

class PlanAdapter(
    private val items: List<PlanCuidado>,
    private val completedIds: MutableSet<Int> = mutableSetOf(),
    private val onToggle: ((planId: Int, done: Boolean) -> Unit)? = null
) : RecyclerView.Adapter<PlanAdapter.ViewHolder>() {

    class ViewHolder(val binding: ItemPlanBinding) :
        RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemPlanBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val plan = items[position]
        val b = holder.binding
        val done = completedIds.contains(plan.id)

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

        b.tvDescripcion.text = plan.descripcion
        b.tvDescripcion.paintFlags = if (done)
            b.tvDescripcion.paintFlags or Paint.STRIKE_THRU_TEXT_FLAG
        else
            b.tvDescripcion.paintFlags and Paint.STRIKE_THRU_TEXT_FLAG.inv()
        b.tvDescripcion.setTextColor(if (done) "#94a3b8".toColorInt() else "#0f172a".toColorInt())
        b.tvFrecuencia.text = plan.frecuenciaDisplay

        (holder.itemView as MaterialCardView)
            .setCardBackgroundColor(if (done) "#f0fdf4".toColorInt() else "#ffffff".toColorInt())

        val px12 = (12 * holder.itemView.resources.displayMetrics.density).toInt()
        val px5 = (5 * holder.itemView.resources.displayMetrics.density).toInt()
        if (plan.tipo == "medicamento") {
            b.tvTipo.text = "MED"
            b.tvTipo.setTextColor(Color.parseColor("#1e40af"))
            b.tvTipo.setBackgroundResource(R.drawable.bg_chip_med)
        } else {
            b.tvTipo.text = "MET"
            b.tvTipo.setTextColor(Color.parseColor("#0891b2"))
            b.tvTipo.setBackgroundResource(R.drawable.bg_chip_met)
        }
        b.tvTipo.setPadding(px12, px5, px12, px5)

        b.checkHecho.setOnCheckedChangeListener(null)
        b.checkHecho.isChecked = done
        b.checkHecho.setOnCheckedChangeListener { _, isChecked ->
            if (isChecked) completedIds.add(plan.id) else completedIds.remove(plan.id)
            notifyItemChanged(position)
            onToggle?.invoke(plan.id, isChecked)
        }
    }

    override fun getItemCount() = items.size
}
