# 01 — Referans kodun durumu

Tarih: 2026-08-13
Depo: https://github.com/kgt1220/Hippocampus_SNN (tek dal `main`, tüm geçmiş çekildi)
Makale: Kim G, Kim P (2025) PLoS Comput Biol 21(7):e1013267
Veri: Zenodo 10.5281/zenodo.14016721 — `Data_final.pkl` (20,3 MB), `Results.egg` (72,2 MB), **kod yok**

## Özet

Yayınlanmış hâliyle koşturulamıyor. Bu bir yorum değil; aşağıdakiler çalıştırılarak
doğrulandı. Ağ kuruluyor (8,2 s, N_CA3=2400) ama ilk CA3 zaman adımında çöküyor.

## Doğrulanan kusurlar

1. **`neuron.py:246` — fazladan yıldız.**
   `np.dot(*self.g_L[n], self.pre_weights[n])` → `TypeError: dot() takes from 2 to 3
   positional arguments but 121 were given`. Aynı işi yapan yedi kardeş satırın
   (239, 245, 257, 262, 267, 272, 277) hiçbirinde `*` yok. Tek karakterlik yazım
   hatası. Klonda düzeltildi — deponun tek değişikliği, `git diff` ile görünür.

2. **`self.W` hiç atanmıyor.** `neuron.py:310-311`'de kullanılıyor, hiçbir yerde
   tanımlanmıyor; `neuron_No_dpp.py:308-309`'da aynısı. Her CA3/CA3i nöron
   güncellemesi `AttributeError` veriyor. Makalenin Denklem 1'inde böyle bir terim
   yok. Yazım hatası değil, **eksik değer** — tahminle doldurulamaz.

3. **`self.qe_max` hiç atanmıyor.** `model.py:287`, STDP ölçek katsayısı. Aynı sınıf.

4. **`Operate_model_v3` hiçbir commit'te yok.** `Simulate_Overlap`,
   `Simulate_EngramNum`, `Simulate_EngramSize`, `Simulate_BiasedInputs` bunu
   çağırıyor — yani Fig 8, 9, 10'u üreten dosyalar. `git log --all --diff-filter=A`
   ile tüm geçmiş tarandı: yalnızca `Operate_model.py` eklenmiş. Son commit'te
   silinen `.pyc` geçmişten kurtarıldı; o da aynı sürümden derlenmiş.

5. **İmza uyuşmazlıkları.** `run_model` 15 konumsal argüman alıyor; not defterleri
   16 ya da 17 ile çağırıyor. `network.solve` 7 tanımlı, `Prepare_Whole_Data.ipynb`
   10 ile çağırıyor.

6. **`Success` / `Fail` hiç güncellenmiyor** — sıfır atanıp sıfır dönüyor. Oysa
   makalenin bütün geri getirme başarısı figürleri bu sayılardan üretiliyor.

7. **`CA3input`, `CA3_R`, `Out_R`, `Out_R_list`** — `Operate_model.py` içinde
   tanımsız. `Simulate_EngramSize.ipynb` bu hatanın izini commit edilmiş hâlde
   taşıyor: `NameError: name 'CA3input' is not defined`.

## Ölçülen hız

İki eksik değeri geçici olarak yamayıp (W=0, qe_max=1) ölçüldü:
**0,658 s / 1 ms zaman adımı**, yani 120 ms'lik tek faz ≈ 79 saniye.

Sebep: vektörize değil — her adımda ~4000 nöron nesnesi Python döngüsünde tek tek
çözülüyor (nöron başına ~162 µs, neredeyse tamamı yorumlayıcı yükü).

Ölçek: makalenin Fig 12'si (100 ipucu × 30 faz) ≈ 66 saat; bizim taramamız
(f × örtüşme × yanlılık × deneme) ≈ 360 saat, tek çekirdek.

## Karar

Tamir edilmedi. İki eksik değeri (`W`, `qe_max`) tahmin etmek dinamiği belirsiz
biçimde değiştirir, ve tamir edilse bile taramalar koşturulamaz. Kendi vektörize
sürümümüz yazıldı — bkz. [02_kendi_modelimiz.md](02_kendi_modelimiz.md).

Klon `reference/Hippocampus_SNN/` altında duruyor; spesifikasyon kaynağı olarak
kullanılıyor (Tablo 1-2-3 + not defterlerindeki `config` sınıfı + `plasticity.py`).
