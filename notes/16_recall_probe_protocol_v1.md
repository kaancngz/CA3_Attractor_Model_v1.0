# CA3 recall–probe testi — protokol ve ilk sonuç v1

Tarih: 2026-08-16
Durum: veri-öncesi mekanistik recall–probe koşusu

Bu koşu yeni bir mimari kurmaz. Dondurulmuş seyrek CA3 çekirdeğini
deneydeki bağlam, ortak ipucu, ışık-kapalı/açık ve opsin-kontrol
mantığıyla yürütür. Her prob ödülsüzdür; ağ durumu prob başında sıfırlanır
ve prob sırasında sinaptik öğrenme yapılmaz.

## Protokol karşılığı

Deney | Hesaplamalı karşılık
--- | ---
Eğitim sonrası bellek | Dondurulmuş A/B Hebbian çekici ağı
Işığın bekleme döneminde başlaması | İpucundan önce 1 soyut güncelleme adımı
Işığın prob boyunca sürmesi | Sürekli pozitif/negatif dış alan
Ödülsüz 3 dakikalık prob | Ödül girdisi olmadan sabit nokta veya kararlı makro-çekici
Aynı hayvanda ışık kapalı/açık | Aynı yapısal ağda eşleşmiş iki koşul
Karşı-dengeleme | Fiziksel A/B, koku ve ışık sırası metaverisi
Kazma ayrım oranı | Pilotla kalibre edilmemiş `β` duyarlılık zarfı

Çalışma noktası: `8.0%` engram seyrekliği, `20.0%` A/B örtüşmesi, `50.0%` RAM etiketleme, `50.0%` fiber erişimi ve `100.0%` tag–test uyumu. Bunların gerçek hücresel kesişimi ortalama `25.0%` etkili nihai-A erişimi üretmiştir.

## Recall yeterlilik kontrolü

A ve B kısmi ipuçları kaldırıldıktan sonra örüntüyü tamamlama oranı: `100.0%` (25/25 ağ).

Sürekli dış alan altında probların `14.2%` kadarı senkron mikrodurum döngüsü üretmiştir. Son faz keyfî seçilmemiş; bir tam döngü üzerinden zaman ortalaması alınmıştır. Bütün problarda çekici sınıfı döngü boyunca kararlı kalmıştır.

## Eşleşmiş prob sonuçları

Kol | Kapalı durum | Açık durum | Ortalama ΔE | Ortalama Δreaktivasyon | ΔDR (`β=2`)
--- | --- | --- | ---: | ---: | ---:
H1_ARCHT_TAGGED_CONTEXT | A | A | -0.203 | -0.407 | -0.100
H2_CHR2_UNTAGGED_CONTEXT | B | A | 1.610 | 0.691 | 1.306
H3_ARCHT_C_TAGGED_LEADING | A | A | -0.550 | -0.480 | -0.339
H3_ARCHT_C_TAGGED_TRAILING | B | B | 0.046 | -0.061 | 0.020
EGFP_TAGGED_CONTEXT_CONTROL | A | A | 0.000 | 0.000 | 0.000
EGFP_UNTAGGED_CONTEXT_CONTROL | B | B | 0.000 | 0.000 | 0.000
EGFP_C_TAGGED_LEADING_CONTROL | A | A | 0.000 | 0.000 | 0.000
EGFP_C_TAGGED_TRAILING_CONTROL | B | B | 0.000 | 0.000 | 0.000

## H3 konumsal etkileşim

- Manipülasyonsuz A-önde/B-geride başlangıç yeterliliği: `100.0%`.
- Ortalama `ΔE_önde−ΔE_geride`: `-0.596`.
- Negatif konumsal etkileşim gösteren yeterli ağ oranı: `100.0%`.

## Hipotez kararı

- **H1:** Baskılama A kanıtını ve etiketli reaktivasyonu azaltır;
  fakat 25/25 ağ A çekicisinde kalır. Minimal nöral gereklilik var,
  güçlü şansa/kategorik çöküş yoktur.
- **H2:** Etkinleştirme 25/25 ağda B çekicisinden A çekicisine geçiş
  üretir; yeterlilik bu çalışma noktasında desteklenir.
- **H3:** A öndeyken baskılama etkisi A gerideykenkinden daha büyüktür;
  fakat 25/25 ağ kendi başlangıç çekicisinde kalır. Pozisyonel asimetri
  var, rakip anıya tam kategorik dönüş yoktur.
- **EGFP:** Bütün eş koşullarda ışık etkisi tam sıfırdır; bu kontrol
  modelde ışığın opsinden bağımsız biyolojik yan etkisini değil,
  manipülasyon alanının yokluğunu temsil eder.

## Çıkarım sınırı

Yapısal ağlar sanal hayvan değildir. Deterministik prob tekrarları
hayvan-içi davranış varyansı, sıra/taşıma etkisi, üç dakikalık kazma
zaman serisi veya 20 Hz optogenetik darbeleri üretmez. Bu nedenle
mevcut tablo mekanistik yön ve çekici geçişini sınar; `p`, Cohen `dz`
ve örneklem büyüklüğü pilot varyansı gelmeden hesaplanmaz.
