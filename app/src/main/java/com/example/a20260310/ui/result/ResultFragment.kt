package com.example.a20260310.ui.result

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.example.a20260310.R
import com.google.android.material.button.MaterialButton

class ResultFragment : Fragment(R.layout.fragment_result) {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        view.findViewById<MaterialButton>(R.id.shareButton).setOnClickListener {
            Toast.makeText(requireContext(), "공유: 더미 동작", Toast.LENGTH_SHORT).show()
        }
        view.findViewById<MaterialButton>(R.id.saveButton).setOnClickListener {
            Toast.makeText(requireContext(), "저장: 더미 동작", Toast.LENGTH_SHORT).show()
        }
    }
}

