# 03 — Ölçek kontrolü: sonuç olumsuz

Tarih: 2026-08-13
Kod: `experiments/03_scale_check.py`

## Soru

Bulduğumuz susturma eğrisi **oranların** mı yoksa **2400 sayısının kendisinin** mi
sonucu? 2400 Kim & Kim'den geldi, elle ayarlanmış bir sayı; gerçek dorsal CA3 çok
daha büyük. Sonuç oranlara bağlıysa aktarılabilir, değilse bir simülasyon
artefaktıdır ve hayvan hakkında hiçbir şey söylemez.

Test: ağla ölçeklenen her şeyi ikiye katla (2400→4800, engram 100→200, bağlantı
sayıları, internöron sayısı), bütün oranları sabit tut, aynı *f* taramasını iki
ağda koş, eğrileri karşılaştır.

## Koşmadan önce yazdığım tahmin

1. Ayrım oranı eğrileri çakışacak.
2. P(fail) büyük ağda **düşecek** — ateşlenme gürültüyle tetikleniyor, hücre
   sayısı ikiye katlanınca birim zamandaki gürültü olayı da ikiye katlanır.

**İkisi de tutmadı.** Eğriler çakışmadı; P(fail) kayda değer biçimde değişmedi
(0.45 vs 0.41, 30 denemede gürültü içinde).

## Yol boyunca bulunan ve düzeltilen üç gerçek hata

1. **İnhibisyon normalize edilmemiş.** Rekürren uyarımı hücre başına sabit
   tutmuştum, inhibisyonu tutmamıştım. Bağlantı *olasılığını* 0.25'te sabitlemek
   yetmiyor: internöron sayısı ikiye katlanınca her uyarıcı hücre 30 yerine 60
   internörondan girdi alıyor, yani hücre başına inhibisyon iki katına çıkıyor.
   Düzeltme: hücre başına toplam inhibitör iletkenliği sabit tut
   (`normalize_inhibition`, `g_ie_total`, `g_ii_total`). Varsayılanlar n_inh=120'de
   referans değerleri birebir üretiyor, yani temel model değişmedi.

2. **Örtüşme kurgusu istenen değeri tutturmuyordu.** `build_engrams` içinde
   B engramının "özel" kısmı yalnızca *paylaşılmak üzere seçilen* hücreleri
   dışlıyordu, A'nın tamamını değil. Sıralama tesadüfen başka A hücrelerini de
   içeri alıyordu. Sonuç: istenen örtüşme 0.10 iken gerçekleşen 0.19, ve bu sapma
   her ağ boyutunda farklıydı. Düzeltildikten sonra gerçekleşen örtüşme istenen
   değere tam eşit.

3. **Engram başına internöron sayısı ölçeklenmemeli.** Seçicilik, engram
   hücrelerinin kendi internöronlarından kaçabilmesine dayanıyor; her biri ağın
   çeyreğine bağlanan *m* internörondan kaçma olasılığı 0.75^m — yani **mutlak
   sayının** fonksiyonu, kesrin değil. *m*'yi 12'den 24'e çıkarmak bu olasılığı
   ~%3'ten ~%0.1'e düşürüyor, engram gerçekte kaçamamış hücrelerden kuruluyor ve
   seçicilik bozuluyor.

## Sonuç

Her düzeltme farkı azalttı ama kapatmadı:

| | en büyük DI farkı |
|---|---|
| A — örtüşme serbest | 0.411 |
| B — örtüşme sabitlenmiş | 0.342 |
| C — + engram başına internöron sabit | **0.227** |

DI'nin toplam oynama aralığı ~0.5 olduğu düşünülürse 0.227 hâlâ büyük.

**Ölçek kontrolü geçmedi.**

## Bunun anlamı

Susturma eşiğini şu an **oranlarla belirlenen bir büyüklük olarak alıntılayamayız.**
"Engramın %X'ini susturmak rekabeti çevirir" cümlesi henüz yazılamaz, çünkü X ağ
boyutuyla değişiyor.

Bu kötü haber değil, kontrolün işini yapması. Üç hata bu sayede bulundu ve
üçü de kontrolden bağımsız olarak zaten hataydı.

## Kalan şüpheliler — sınanmadı

1. **Seçicilik hâlâ ölçek-değişmez değil.** *m* sabit tutulunca bu sefer
   internöronların *kesri* değişiyor (12/120 = %10 vs 12/240 = %5), yani bir
   engramın rakibi üzerinde uyguladığı bastırma farklılaşıyor. Kaçma olasılığı ile
   bastırma gücü aynı anda sabit tutulamıyor olabilir — öyleyse bu, kurgunun
   yapısal bir sınırı.
2. **Okuma ölçütü mutlak.** `winner()` engram ortalamasının ≥ 25 Hz olmasını
   istiyor. Bu, farklı boyuttaki ağlara uygulanan mutlak bir eşik; ateşleme hızı
   sistematik olarak kayıyorsa sınıflandırma da kayar. Ucuz bir kontrol, henüz
   yapılmadı.
3. **Ateşlenme dinamiği.** Çekiciyi ayakta tutmak için eşzamanlı ateşlemesi
   gereken hücre sayısı ağ boyutuyla doğrusal ölçeklenmiyor olabilir.

## Blok C'de dikkat çeken bir yan bulgu

*m* sabitlenince 4800'lük ağ daha yetkin davranıyor: f=0 iken P(fail) 0.20'ye
düşüyor (2400'de 0.43) ve *f* arttıkça DI düzgün, tek yönlü biçimde +0.15'ten
−0.29'a iniyor, sıfırı ~f=0.25'te geçerek. Yani büyük ağda **kademeli ve
monoton** bir susturma eğrisi var; küçük ağda eğri neredeyse düz.

Eğer bu doğrulanırsa, 2400'lük ağın rekabeti çözmek için fazla küçük olduğu
anlamına gelir — ve asıl sorun ölçek bağımlılığı değil, **temel ağın yetersizliği**
olabilir. Bir sonraki adımın hedefi bu olmalı.
