package com.example.croniccare.utils

object AppColors {

    object Critical {
        const val text = "#dc2626"
        const val bg = "#fee2e2"
        const val stroke = "#fca5a5"
    }

    object Warning {
        const val text = "#d97706"
        const val bg = "#fef3c7"
        const val stroke = "#fcd34d"
    }

    object Leve {
        const val text = "#ca8a04"
        const val bg = "#fefce8"
    }

    object Ok {
        const val text = "#16a34a"
        const val bg = "#dcfce7"
        const val stroke = "#86efac"
    }

    object Via {
        val oral = "#dbeafe" to "#1e40af"
        val inhalada = "#dcfce7" to "#16a34a"
        val iv = "#fce7f3" to "#be185d"
        val sc = "#f3e8ff" to "#7c3aed"
        val im = "#fff7ed" to "#c2410c"
        val default = "#f1f5f9" to "#475569"
    }
}
