# 04 — Modelimiz ile veri güdümlü CA3 arasındaki fark

Tarih: 2026-08-13
Kaynak: Kopsick ve ark. (2023) Cognit Comput 15(4):1190-1210, Tablo 1-4.
Değerler: [params/hippocampome_ca3.yaml](../params/hippocampome_ca3.yaml)

Hippocampome.org'un `counts.php` ve `connprob.php` sayfaları parola korumalı.
Ama makale bu sayıları tablo hâlinde yayınlamış; PDF'ten birebir okundu.

## Üç yapısal parametremiz büyük çarpanlarla yanlış

| | bizim modelimiz | veri güdümlü CA3 | fark |
|---|---|---|---|
| Uyarıcı/inhibitör oranı | 20 : 1 | **5 : 1** | 4 kat az internöron |
| Rekürren bağlantı olasılığı (piramidal→piramidal) | 0,25 | **0,025** | 10 kat fazla yoğun |
| Piramidal hücre sayısı | 2400 | **74.366** | %3,2'sindeyiz |

İlk ikisi ölçekle ilgisiz — oran hatası. Yani ağı büyütmek bunları düzeltmez.

## Nöron parametreleri de aynı nöron değil

| | bizim (Kim & Kim) | veri güdümlü (Tablo 2) |
|---|---|---|
| C | 80 | **366** |
| k | 3 | **0,792** |
| b | +5 | **−42,552** |
| d | 10 | **588** |
| v_peak | 50 | **35,861** |

`b` işaret değiştiriyor. Bu bir ölçek farkı değil, niteliksel olarak başka bir
hücre — Izhikevich modelinde `b < 0` farklı bir uyarılabilirlik/rezonans rejimi
demek.

## Elimize geçen diğer şeyler

- **Yedi internöron tipinin ayrı ayrı popülasyon büyüklükleri** ve 51 bağlantı
  tipinin olasılıkları. Bizim tek bir "internöron" havuzumuz var; gerçekte
  perisomatik hedefleyenler (basket, akso-aksonik, CCK+) piramidal hücrelere
  0,150 olasılıkla bağlanırken bistratified 0,028 ile bağlanıyor. Beş kat fark.
- **Kısa süreli plastisite parametreleri** (Tsodyks-Markram) her bağlantı tipi
  için. Bizim modelimizde kısa süreli plastisite hiç yok.
- **Biyolojik kalibrasyon hedefi:** ağın dinlenme hâli ortalama ateşleme hızı
  ~3 Hz. Bu, şu an kalibre ettiğimiz "%80 geri getirme başarısı"ndan çok daha
  iyi bir hedef — çünkü bir model çıktısı değil, bir gözlem.

## Bunun ölçek kontrolüyle bağlantısı

[notes/03](03_olcek_kontrolu.md)'te ölçek kontrolü geçmemişti ve sebebini
bulamamıştım. Şimdi iki güçlü aday var:

1. **Rekürren bağlantı 10 kat fazla yoğun.** 0,25 olasılıkla her hücre kendi
   engramının dörtte biriyle bağlantılı. Engram büyüdükçe bu, hücre başına gelen
   rekürren girdiyi patlatıyor — normalizasyonla bastırmaya çalıştığım şey tam
   olarak buydu. Gerçek değerde (0,025) bu sorun büyük ölçüde kendiliğinden
   kaybolabilir.
2. **İnternöron sayısı 4 kat az.** Rekabet inhibisyon üzerinden çözülüyor;
   inhibitör havuz gereğinden küçükse rekabet zayıf ve ağ boyutuna duyarlı olur.

Yani ölçek kontrolünün başarısızlığı bir "ölçek sorunu" değil, **yanlış oranlar**
sorunu olabilir. Sınanmadı.

## Kod tarafı: alınmadı, gerekçesi

CARLsim4 dalı CUDA 10.1 ve compute capability 7.0 istiyor; makalede 32 GB
VRAM'li Tesla V100 üzerinde, 20'den fazla böyle GPU'su olan bir HPC kümesinde
koşturulmuş. Buradaki donanım RTX 5070 (12 GB, Blackwell, compute capability
12.0). CUDA 10.1 2019'dan ve Blackwell'i hedefleyemez. Analiz deposu da MATLAB
istiyor.

Port etmek mümkün (CARLsim6 modern CUDA destekliyor) ama günler alır ve sonunda
okunamayan bir C++/CUDA yığını kalır. Parametreleri aldık, kodu almadık.

## Yapılmadı

Bu değerlerin hiçbiri `src/ca3` içine bağlanmadı. Bağlamak modelin davranışını
değiştirir ve yeniden kalibrasyon gerektirir — ayrı bir adım, ayrı bir karar.
