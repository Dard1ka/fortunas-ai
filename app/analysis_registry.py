ANALYSIS_REGISTRY = {
    "repeat_customer": {
        "label": "Analisis Pelanggan Loyal",
        "description": "Mencari pelanggan yang paling sering belanja dan melihat pola produk yang paling sering mereka beli.",
        "enabled": True,
    },
    "high_value_customer": {
        "label": "Analisis Pelanggan Paling Bernilai",
        "description": "Mencari pelanggan dengan total belanja tertinggi dan melihat pola produk favorit mereka.",
        "enabled": True,
    },
    "peak_hour": {
        "label": "Analisis Jam Ramai",
        "description": "Mencari jam transaksi paling ramai dan produk yang paling sering dibeli pada jam tersebut.",
        "enabled": True,
    },
    "bundle_opportunity": {
        "label": "Analisis Produk yang Cocok Dibundling",
        "description": "Mencari pasangan produk yang paling sering dibeli bersama untuk dijadikan bundling atau cross-sell.",
        "enabled": True,
    },
    "top_product": {
        "label": "Analisis Produk Terlaris",
        "description": "Mencari produk dengan kontribusi omzet tertinggi beserta jumlah unit terjual, untuk fokus stok dan promosi.",
        "enabled": True,
    },
    "revenue_trend": {
        "label": "Analisis Tren Omzet",
        "description": "Melihat tren omzet harian 30 hari terakhir beserta jumlah transaksi, untuk memantau naik-turunnya penjualan.",
        "enabled": True,
    },
    "customer_segmentation": {
        "label": "Analisis Segmentasi Pelanggan (RFM)",
        "description": "Mengelompokkan pelanggan menjadi champions, loyal, at-risk, dan churned berdasarkan recency-frequency-monetary.",
        "enabled": True,
    },
    "churn_risk": {
        "label": "Analisis Risiko Churn",
        "description": "Mencari pelanggan yang dulu aktif tetapi sudah lama tidak belanja, untuk ditarget kampanye reaktivasi.",
        "enabled": True,
    },
    "slow_moving_product": {
        "label": "Analisis Produk Slow-Moving",
        "description": "Mencari produk yang sudah lama tidak laku, kandidat diskon atau bundling.",
        "enabled": True,
    },
    "average_basket_size": {
        "label": "Analisis Ukuran Keranjang Rata-rata",
        "description": "Menghitung rata-rata jumlah item dan nilai belanja per transaksi.",
        "enabled": True,
    },
    "demand_forecast": {
        "label": "Analisis Prediksi Permintaan",
        "description": "Memperkirakan permintaan produk minggu depan memakai rata-rata penjualan mingguan (moving average).",
        "enabled": True,
    },
}
