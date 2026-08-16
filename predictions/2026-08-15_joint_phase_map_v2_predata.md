# Veri-öncesi koşullu öngörüler — birleşik H1–H3 faz haritası v2

Tarih: 2026-08-15
Durum: dondurulmuş v2; deney ve pilot verisi görülmeden yazıldı

Bu dosya v1 öngörülerini silmez. Aynı dondurulmuş seyrek CA3 mimarisini daha
geniş bir `örtüşme × etkili erişim × manipülasyon gücü` uzayında sınar ve
hipotezlerin zayıf ve güçlü biçimlerini önceden ayırır. Sonuç geldikten sonra
bu dosya değiştirilmez; düzeltme gerekirse yeni bir sürüm eklenir.

## Değişmeyen model sözleşmesi

- İki eşit seyrek A/B örüntüsü, merkezlenmiş covariance-Hebbian rekürrens ve
  `W_ii=0`.
- Hızlı global inhibisyonun indirgenmiş karşılığı olan seyrek etkinlik tavanı.
- H1–H3 görülmeden önce bağımsız çekici kapılarıyla seçilmiş
  `activation_threshold=0,12`.
- RAM verimi, fiber erişimi ve çıplak-A/test-A uyumu ayrı ilkelerdir. Birleşik
  taramadaki **etkili erişim**, bunların son A engramında gerçekten erişilebilir
  kesişimidir; dördüncü bir biyolojik süreç değildir.
- H1–H3 sonucuna uydurulmuş parametre sayısı sıfırdır. Örtüşme, etkili erişim
  ve güç sonuç seçmek için ayarlanmaz; faz ekseni olarak taranır.
- Her ışık-açık sonucu aynı yapısal ağın ışık-kapalı sonucuyla eşleştirilir.
  A/B örüntüleri simetriktir; H3'te A'nın önde ve geride olduğu iki ton ataması
  birlikte sınanır.

Tarama 10 örtüşme, 15 etkili erişim ve 5 güç düzeyinden oluşan 750 birleşik
koşulu içerir. Her koşul aynı 25 yapısal gerçekleştirimde sınanmıştır. Bu 25
ağ, hayvan örneklemi, biyolojik varyans, p-değeri veya güç analizi değildir.

## Birincil veri-öncesi çalışma noktası

- Engram seyrekliği: `%8`
- A/B örtüşmesi: `%20`
- Etkili nihai-A erişimi: `%25`
- Manipülasyon gücü: `1,0` normalize model birimi
- Ton desteği: `%65/%35` ve karşı-denk `%35/%65`

Davranışsal ayrım oranı için `β=1, 2, 4, 8` bir duyarlılık zarfıdır. Pilot
kalibrasyonu gelmeden bu dört eğriden biri “beklenen gerçek davranış” diye
seçilmez.

## H1 — gereklilik

H1'in iki ayrı iddiası vardır:

1. **Minimal nöral gereklilik:** A engramının erişilebilir kesimini susturmak
   A yönlü mutlak geri-getirme kanıtını ve etiketli reaktivasyonu azaltır.
2. **Güçlü davranışsal/kategorik biçim:** aynı müdahale A çekicisini bozar ve
   tercihi şans düzeyine indirir.

Birincil noktada modelin koşullu öngörüsü:

- `ortalama ΔE = -0,24`,
- `ortalama Δη_etiketli = -0,23`,
- A çekicisi dışına çıkan ağ oranı `%4`,
- şansa-yakın kanıt oranı `%0`.

Dolayısıyla minimal H1 desteklenir; özgün güçlü “şansa çöküş” biçimi bu
çalışma noktasında desteklenmez. `%20` örtüşme ve güç `1,0` kesitinde ağların
çoğunda A dışına çıkış yaklaşık `%50` etkili erişimde oluşur; ağların çoğunda
şansa-yakın kanıt taranan `%0–%50` erişim aralığında oluşmaz.

**Çürütücü gözlem:** Hücresel örtüşme yaklaşık `%20`, etkili erişim yaklaşık
`%25` ve nöral baskılama doğrulanmışken tekrarlanabilir şansa-yakın/kategorik
çöküş görülmesi, rastgele-dağıtık etiketli hücre sürümünü reddeder. Böyle bir
sonuç seçici hub/çekirdek hücre erişimi, erişim hesabının eksikliği veya
ağ-yayılımlı optogenetik etki gerektirir.

## H2 — yeterlilik

Birincil noktada A etiketi B zemininde etkinleştirildiğinde:

- `ortalama ΔE = +1,61`,
- 25/25 ağ B'den A çekicisine geçer,
- `β=2` duyarlılık zarfında beklenen ayrım değişimi yaklaşık `+1,31` olur;
  bu son sayı pilot davranışı değildir.

`%20` örtüşme ve güç `1,0` kesitinde ağların en az `%80`'inde A çekicisi
seçimi için etkili erişim eşiği `%22,5`'tir.

**Çürütücü gözlem:** Etkili erişim `≥%22,5` ve etkinleştirme gücü karşılaştırılabilir
olduğu doğrulandığı hâlde A yönlü nöral veya davranışsal kayma bulunmaması
mevcut yeterlilik yüzeyini reddeder.

## H3 — rekabet ve mevcut konuma bağlı asimetri

H3'ün iki ayrı iddiası vardır:

1. **Pozisyonel asimetri:** A öndeyken A-susturmanın etkisi, A gerideykenki
   etkiden daha negatiftir.
2. **Güçlü rakibe dönüş:** A öndeyken aynı müdahale sistemi kategorik olarak
   B çekicisine geçirir.

Önce manipülasyonsuz `%65/%35` ve `%35/%65` koşullarının sırasıyla A ve B
çekicisini seçmesi gerekir. Bu başlangıç ayrışması yoksa H3 o koşulda test
edilemez; sıfır örtüşme ablasyonunda olan tam olarak budur.

Birincil noktada:

- başlangıç ayrışması 25/25 ağda geçerlidir,
- A öndeyken `ΔE = -0,55`,
- A gerideyken `ΔE = +0,05`,
- imzalı etkileşim `I = ΔE_önde - ΔE_geride = -0,60`,
- pozisyonel asimetri 25/25 ağda doğru yöndedir,
- kategorik B'ye geçiş 0/25'tir.

Dolayısıyla H3'ün konuma bağlı asimetri biçimi desteklenir; güçlü “rakip
anıya tam dönüş” biçimi birincil noktada desteklenmez. Varsayılan kesitte
pozisyonel etkileşim `%5` erişimden itibaren görülür; ağların en az `%80`'inde
B'ye tam dönüş `%50` erişime kadar oluşmaz.

**Çürütücü gözlem:** Manipülasyonsuz A-önde/B-geride başlangıçları kurulmuşken
`I ≥ 0` bulunması pozisyonel asimetri öngörüsünü reddeder.

## Mekanizma bağımlılıkları

- Rekürrens sıfırlandığında sabit noktalar, kısmi ipucundan tamamlama ve yerel
  havza dönüşü kaybolmalıdır. Mevcut ablasyonda bütün geçerlik kapılarını geçen
  ağ oranı `%100`'den `%0`'a düşer.
- Seyrek inhibisyon kaldırıldığında H2 seçici A geri-getirmesi yerine karışık
  etkinlik üretmelidir. Mevcut ablasyonda H2 ağlarının `%100`'ü `mixed` olur.
- Örtüşme sıfırlandığında A ve B ayrı ayrı geri getirilebilir; fakat seçilen
  `%65/%35` ton rejimi H3 başlangıç rekabetini kurmamalıdır. Bu nedenle H3
  etkileşimi o koşulda “sıfır” değil, **tanımsız/test edilemez** sayılır.

Bu üç sonuçtan biri pilotla değiştirilmemiş çekirdekte tersine dönerse ilgili
mekanizmanın nedensel açıklamadaki yeri yeniden değerlendirilir.

## Pilot verisi gelince kilitlenecek girdiler

1. A/B hücresel örtüşmesi ve engram seyrekliği.
2. RAM etiketleme verimi, fiber/ekspresyon erişimi ve çıplak-A/test-A uyumu;
   bunlardan etkili erişim hesaplanır.
3. ArchT/ChR2'nin gerçek nöral etki büyüklüğünü normalize güce bağlayan
   kalibrasyon.
4. `%65/%35` ton programının oluşturduğu başlangıç yanlılığı ve ton yokluğu
   için `full_contingency`–`presence_only` ayrımı.
5. Nöral kanıt `E` ile kazma ayrım oranı arasındaki eğim (`β`) ve aynı hayvan
   içindeki ışık-açık/kapalı farkların varyansı.

Bu değerler gelmeden Cohen `dz`, gerekli `n` veya tek bir davranışsal etki
büyüklüğü raporlanmaz. Modelin bugünkü çıktısı, biyolojik etki tahmini değil;
ölçülen pilot girdilerin yerleştirileceği ve sonra yanlışlanabilecek koşullu
bir öngörü yüzeyidir.
