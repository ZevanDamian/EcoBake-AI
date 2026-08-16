import gradio as gr
import google.generativeai as genai
import json
import os
import re

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

def prediksi_produksi(produk, terjual_kemarin, harga, hari, cuaca, musim, promo, sisa_buang):
    if not API_KEY or API_KEY == "MASUKKAN_API_KEY_DI_SINI":
        return ("⚠️ ERROR", "N/A", "N/A", "N/A", "API Key belum dikonfigurasi pada environment variable.")

    prompt_instruksi = f"""
    Bertindaklah sebagai AI Demand & Food Waste Predictor untuk industri Bakery & Pastry.
    Tugas Anda adalah memberikan rekomendasi jumlah produksi harian yang presisi untuk meminimalisir Food Waste.

    Data Operasional Toko Hari Ini:
    - Jenis Produk: {produk}
    - Terjual Kemarin: {terjual_kemarin} unit
    - Harga Produk: Rp{harga}
    - Hari Operasional Besok: {hari}
    - Kondisi Cuaca Besok: {cuaca}
    - Event/Musim: {musim}
    - Status Promo: {promo}
    - Sisa Stok Kemarin (Dibuang): {sisa_buang} unit

    Berdasarkan korelasi data di atas, lakukan kalkulasi prediktif. 
    WAJIB KELUARKAN HANYA FORMAT JSON MURNI (tanpa markdown, tanpa teks pembuka/penutup). 
    Gunakan struktur eksak berikut:
    {{
        "expected_demand": <angka integer>,
        "recommended_production": <angka integer>,
        "overstock_risk": "<TINGGI / SEDANG / RENDAH>",
        "food_waste_reduction_est": "<persentase string, misal 22%>",
        "strategic_insight": "<2-3 kalimat analisis logis gabungan cuaca, hari, dan tren kemarin>"
    }}
    """

    try:
        respons = model.generate_content(prompt_instruksi)
        teks_output = respons.text

        match = re.search(r'\{.*\}', teks_output, re.DOTALL)
        if match:
            clean_json = match.group(0)
        else:
            clean_json = teks_output.replace("```json", "").replace("```", "").strip()
            
        data = json.loads(clean_json)

        exp_demand = str(data.get("expected_demand", 0))
        rec_prod = str(data.get("recommended_production", 0))
        risk = data.get("overstock_risk", "TIDAK DIKETAHUI")
        waste_est = data.get("food_waste_reduction_est", "0%")
        insight = data.get("strategic_insight", "Analisis tidak tersedia.")

        risk_color = "🔴 " if "TINGGI" in risk else "🟡 " if "SEDANG" in risk else "🟢 "
        risk_display = risk_color + risk

        return exp_demand, rec_prod, risk_display, waste_est, insight

    except json.JSONDecodeError:
        return ("⚠️ GAGAL", "N/A", "N/A", "N/A", f"Gagal memparsing JSON dari AI. Respons mentah: {teks_output}")
    except Exception as e:
        return ("⚠️ ERROR", "N/A", "N/A", "N/A", f"Terjadi kesalahan sistem: {str(e)}")

with gr.Blocks(theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="amber")) as app:
    gr.Markdown("# 🥐 EcoBake AI: Demand & Food Waste Predictor")
    gr.Markdown("Sistem rekomendasi produksi *Bakery & Pastry* cerdas berbasis LLM untuk menekan limbah makanan (*Food Waste*) dan memaksimalkan profitabilitas operasional harian.")
    
    with gr.Row():
        with gr.Column(scale=1, variant="panel"):
            gr.Markdown("### 📊 Parameter Input Operasional")
            
            in_produk = gr.Dropdown(choices=["Butter Croissant", "Sourdough Bread", "Bomboloni", "Choco Muffin"], label="1. Jenis Produk", value="Butter Croissant")
            
            with gr.Row():
                in_terjual = gr.Number(label="2. Terjual H-1 (Unit)", value=45)
                in_sisa = gr.Number(label="8. Stok Dibuang H-1 (Unit)", value=12)
                
            in_harga = gr.Number(label="3. Harga Produk (Rp)", value=25000)
            in_hari = gr.Dropdown(choices=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"], label="4. Hari Operasional Besok", value="Senin")
            in_cuaca = gr.Dropdown(choices=["Cerah Terik", "Mendung", "Hujan Lebat/Badai"], label="5. Prakiraan Cuaca Besok", value="Hujan Lebat/Badai")
            in_musim = gr.Dropdown(choices=["Hari Kerja Normal", "Akhir Pekan", "Libur Nasional", "Tanggal Muda"], label="6. Event / Musim", value="Hari Kerja Normal")
            in_promo = gr.Dropdown(choices=["Tidak Ada", "Buy 1 Get 1", "Diskon 50% Malam"], label="7. Status Promo", value="Tidak Ada")
            
            btn_prediksi = gr.Button("🚀 Hasilkan Rekomendasi Produksi", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("### 🧠 AI Analytics Dashboard")
            
            with gr.Row():
                out_rec_prod = gr.Textbox(label="Rekomendasi Produksi Besok (Unit)", lines=1)
                out_exp_demand = gr.Textbox(label="Proyeksi Permintaan Pasar (Unit)", lines=1)
                
            with gr.Row():
                out_risk = gr.Textbox(label="Risiko Overstock (Food Waste)", lines=1)
                out_waste_est = gr.Textbox(label="Estimasi Penurunan Food Waste", lines=1)
                
            out_insight = gr.Textbox(label="💡 Strategic Insight (Root Cause Analysis)", lines=5)

    btn_prediksi.click(
        fn=prediksi_produksi,
        inputs=[in_produk, in_terjual, in_harga, in_hari, in_cuaca, in_musim, in_promo, in_sisa],
        outputs=[out_exp_demand, out_rec_prod, out_risk, out_waste_est, out_insight]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
