package com.example.a20260310.ui.home

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.a20260310.R
import com.example.a20260310.ui.common.SimpleRow
import com.example.a20260310.ui.common.SimpleRowAdapter

class HomeFragment : Fragment(R.layout.fragment_home) {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val items = listOf(
            SimpleRow(title = "캡스톤 킥오프", subtitle = "2026-04-01 • 42분 • 요약 생성됨"),
            SimpleRow(title = "디자인 리뷰", subtitle = "2026-03-28 • 30분 • 액션 5개"),
            SimpleRow(title = "주간 스탠드업", subtitle = "2026-03-25 • 12분 • 요약 생성됨"),
        )

        view.findViewById<RecyclerView>(R.id.recycler).apply {
            layoutManager = LinearLayoutManager(context)
            adapter = SimpleRowAdapter(items)
        }
    }
}

