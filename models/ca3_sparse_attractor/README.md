# Birincil seyrek CA3 çekici modeli

Bu klasör, projenin README'sinde “Katman 1 — projenin omurgası” olarak tarif
edilen bağımsız hücre-düzeyi otoasosiyatif modeli içerir.

Modelin kuramsal bileşenleri:

- iki eşit büyüklükte, kısmen örtüşen ikili A/B engramı,
- standart merkezlenmiş Hebbian/covariance rekürren ağırlık kuralı,
- hızlı global inhibisyonun indirgenmiş karşılığı olarak seyrek etkinlik tavanı,
- kısmi ipucundan sabit noktaya örüntü tamamlama,
- ayrı çıplak-A etiket kaynağı, RAM verimi, test-A uyuşması ve fiber erişimi,
- etiketli altkümenin aktivasyonu veya susturulması,
- çekici kimliği, mutlak geri-getirme kanıtı ve etiketli reaktivasyon için ayrı
  okumalar; mutlak kanıt ile davranışsal ayrım arasında ayrı ölçüm modeli.

Yoğun `N×N` ağırlık matrisi kurulmaz. Öz-bağlantıları sıfırlanmış (`W_ii=0`)
iki-örüntülü yoğun Hebbian matrisin alanı matematiksel olarak tam eşdeğer
faktörize biçimde hesaplanır; bu nedenle 10.000 hücre profili de hafiftir.

Bağımsız geçerlik taraması:

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_validation `
  --profile pilot `
  --output .\outputs\ca3_sparse_attractor\independent_validation_pilot_v1.json
```

λ havzası ve H1-H3 yüzeyleri:

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_theory_experiments `
  --profile pilot `
  --output .\outputs\ca3_sparse_attractor\theory_experiments_pilot_v2.json
```

Dondurulmuş mimarinin seyreklik × örtüşme sağlamlığı:

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_robustness `
  --output .\outputs\ca3_sparse_attractor\robustness_overlap_sparsity_v1.json
```

Çalışma noktası `activation_threshold=0.12`, H1-H3 görülmeden önce 5 tohumda
geçen `0.08–0.16` bandının orta noktası olarak seçildi. Engram oranı, örtüşme,
RAM verimi, fiber erişimi, tag-test uyuşması ve davranış okuma eğimi biyolojik
ölçüm değildir; pilot/serbest parametredir.

Mevcut sağlamlık taramasında `%4–%12` seyreklik ve `%0–%60` örtüşmenin tümü
bağımsız çekici kapılarını geçti. Buna karşılık örtüşme H1 etki büyüklüğünü ve
H3'ün 65/35 ipucuyla kurulmasını belirledi; bu nedenle biyolojik pilotta
ölçülmesi gereken moderatördür, ayarlanacak bir “sonuç uydurma” düğmesi değildir.

## Hipotez sınama hattı

Yeni bir mimari kurmadan, aynı dondurulmuş çekirdek üzerinde birleşik faz
haritasını üretmek için:

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_hypothesis_phase_map `
  --output .\outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json
```

Karar raporu, mekanizma ablasyonları ve parametre rol denetimi:

```powershell
& .\.venv\Scripts\python.exe `
  .\analysis\summarize_hypothesis_phase_map.py `
  --input .\outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json `
  --json-output .\outputs\ca3_sparse_attractor\hypothesis_decision_report_v1.json `
  --markdown-output .\notes\15_hypothesis_decision_report_v1.md

& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_mechanism_ablations `
  --output .\outputs\ca3_sparse_attractor\mechanism_ablations_v1.json

& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.parameter_audit `
  --output .\outputs\ca3_sparse_attractor\parameter_audit_v1.json
```

Faz figürünü ve etkileşimli hipotez laboratuvarını yeniden oluşturmak için:

```powershell
& .\.venv\Scripts\python.exe `
  .\analysis\plot_hypothesis_phase_map.py `
  --input .\outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json `
  --strength 1.0 `
  --output .\outputs\ca3_sparse_attractor\hypothesis_phase_map_strength1_v1.png

& .\.venv\Scripts\python.exe `
  .\analysis\build_ca3_hypothesis_lab.py `
  --phase-map .\outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json `
  --ablations .\outputs\ca3_sparse_attractor\mechanism_ablations_v1.json `
  --template .\analysis\templates\ca3-hypothesis-lab.fragment.html `
  --output .\apps\ca3_hypothesis_lab.fragment.html `
  --standalone-output .\apps\ca3_hypothesis_lab.html
```

Birincil nokta `%20` örtüşme, `%25` etkili erişim ve güç `1,0`'dır. Bu
değerler “en iyi sonuç” için fit edilmemiştir; faz haritasındaki işaretli bir
referans kesittir. 25 yapısal ağ aynı ışık-kapalı/açık çiftinde kullanılır.
Yapısal ağlar hayvan varyansı değildir ve pilot gelmeden `dz` üretmez.

Güncel kararlar:

- H1: kısmi nöral gereklilik var; varsayılan noktada şansa çöküş yok.
- H2: A'ya kategorik geçiş var; `%20` örtüşmede yaklaşık eşik `%22,5` etkili
  erişim.
- H3: konuma bağlı asimetri var; varsayılan noktada rakip B'ye tam geçiş yok.

`no_recurrence`, `no_sparse_inhibition` ve `zero_overlap` kontrolleri sonuçların
sırasıyla çekici rekürrensine, seçici rekabete ve H3'ün kurulabildiği ortak
temsil zeminine bağlı olduğunu sınar. Tüm yapılandırma ve dış eşleme
parametreleri `parameter_audit.py` tarafından sınıflandırılır; H1–H3'e fit
edilmiş parametre sayısı sıfır olmak zorundadır.

## Deney eşlemeli recall–probe protokolü

Bu koşu, ağırlıkları değiştirmeden önce A/B örüntü tamamlama yeterliliğini
sınar; ardından H1, H2, H3 ve EGFP aynalarını aynı yapısal ağ içinde eşleşmiş
ışık-kapalı/açık problarla yürütür:

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_recall_probe_protocol `
  --json-output .\outputs\ca3_sparse_attractor\recall_probe_protocol_v1.json `
  --csv-output .\outputs\ca3_sparse_attractor\recall_probe_trials_v1.csv `
  --markdown-output .\notes\16_recall_probe_protocol_v1.md

& .\.venv\Scripts\python.exe `
  .\analysis\plot_recall_probe_protocol.py `
  --input .\outputs\ca3_sparse_attractor\recall_probe_protocol_v1.json `
  --output .\outputs\ca3_sparse_attractor\recall_probe_protocol_v1.png
```

Problar ödülsüzdür, her prob öncesi dinamik durum sıfırlanır ve prob sırasında
plastisite yoktur. Işık bir soyut güncelleme adımı önce başlar ve ipucuyla
birlikte sürer; bu adım 10–20 saniyenin biyofiziksel karşılığı değildir,
yalnızca deneysel olay sırasını korur. Fiziksel A/B etiketi, ödüllü koku ve
ışık sırası karşı-dengelenir. Aynı tohumların farklı vektör kollarında yeniden
kullanılması mekanistik karşı-olgusal bloklamadır; tek hayvanın bütün gruplara
girdiği anlamına gelmez.

Sürekli dış alan altındaki senkron ikili güncellemeler kısa mikrodurum
döngüleri üretebilir. Protokol son fazı keyfî seçmez; tam döngü ortalamasını
okur ve çekici sınıfının döngü boyunca sabit kalmasını kalite kapısı olarak
zorunlu tutar.
