package com.example.croniccare

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.navigation.NavOptions
import androidx.navigation.fragment.NavHostFragment
import com.example.croniccare.data.network.AuthEventBus
import com.example.croniccare.databinding.ActivityMainBinding
import com.example.croniccare.utils.SessionManager
import com.example.croniccare.utils.applyNavBarBottomPadding
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.bottomNav.applyNavBarBottomPadding()

        session = SessionManager(this)

        val navHost = supportFragmentManager.findFragmentById(R.id.navHostFragment) as NavHostFragment
        val navController = navHost.navController

        val navOptions = NavOptions.Builder()
            .setEnterAnim(R.anim.nav_fade_in)
            .setExitAnim(R.anim.nav_fade_out)
            .setPopEnterAnim(R.anim.nav_fade_in)
            .setPopExitAnim(R.anim.nav_fade_out)
            .setLaunchSingleTop(true)
            .setRestoreState(true)
            .setPopUpTo(R.id.nav_dashboard, inclusive = false, saveState = true)
            .build()

        binding.bottomNav.setOnItemSelectedListener { item ->
            navController.navigate(item.itemId, null, navOptions)
            true
        }

        navController.addOnDestinationChangedListener { _, destination, _ ->
            binding.bottomNav.menu.findItem(destination.id)?.isChecked = true
        }

        lifecycleScope.launch {
            AuthEventBus.unauthorized.collect {
                session.clearSession()
                navigateToLogin()
            }
        }
    }

    fun navigateToLogin() {
        startActivity(Intent(this, LoginActivity::class.java))
        finish()
    }
}
