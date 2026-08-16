# Veri-öncesi koşullu öngörüler — seyrek CA3 çekici v1

Tarih: 2026-08-15
Durum: dondurulmuş v1; deney/pilot verisi görülmeden yazıldı

Bu dosya sonuç geldikten sonra değiştirilmez. Düzeltme gerekirse yeni tarihli
bir sürüm eklenir.

## Sabit kuramsal koşullar

- İki eşit, %8 seyrek A/B örüntüsü; başlangıç örtüşmesi %20.
- `W_ii=0` merkezlenmiş Hebbian/covariance rekürrens.
- Etkinlik tavanı %8.
- Bağımsız geçerli platonun orta noktası `threshold=0,12`.
- Eğitim olasılığı, sabit toplam afferent hedef bütçesine normalize destek
  (`λ`) olarak çevrilir.
- H1-H3, parametre seçiminde kullanılmadı.

## P1 — ton varlığının yönü

Eşit A/B deney sayısı ve öğrenilmiş desteğin eğitim frekansını yansıttığı
koşulda `%65/%35` ton, C'de 5/5 ağda yüksek olasılıklı bağlam çekicisini seçer.

Çürütücü gözlem: pilotta ton yönü hayvanlar arasında karşı-dengelemeden sonra
yüksek olasılıklı bağlamı sistematik biçimde yordamaz.

## P2 — ton yokluğu

- `full_contingency`: yokluk tercih yönünü tersine çevirir.
- `presence_only`: yokluk nötr/sınır durumudur.

Bu iki öngörü rakiptir; deney hangisini desteklerse diğeri reddedilir.

## P3 — H1

Sabit `%20` A/B örtüşmesi koşulunda, etkili olarak nihai A engramının en fazla
%25'i susturuluyorsa A bağlamının sürekli girdisi altında A çekicisi 5/5 ağda
kategorik olarak korunur; fakat geri-getirme gücü ve reaktivasyon azalır.
Etkili %25 erişimde:

- `strength=1`: `ΔA-engram ≈ -0,20`, `Δetiketli reaktivasyon ≈ -0,40`,
  `ΔE ≈ -0,20`,
- `strength=4`: `ΔA-engram ≈ -0,25`, `Δetiketli reaktivasyon ≈ -0,50`,
  `ΔE ≈ -0,25`.

Dolayısıyla öngörü “etki yok” değil; **kısmi nöral zayıflama var, kategorik
anı/tercih çöküşü yok**tur.

Çürütücü gözlem: histoloji/erişim hesabıyla etkili nihai-A oranı ≤%25 iken,
ölçülen kısmi reaktivasyon kaybıyla açıklanamayacak şansa-yakın davranış veya
kategorik A-çekici çöküşü.

## P4 — H2

Rastgele erişilen nihai-A hücre oranı yaklaşık %20 civarında geçiş bandına,
%25 civarında güvenilir A çekicisi seçimine ulaşır. Nominal %25 erişim:

- tag-test eşleşmesi %100: etkili %25, 5/5 A,
- eşleşme %75: etkili ~%18, 2/5 A,
- eşleşme %50: etkili ~%12, 0/5 A.

Çürütücü gözlem: etkili oran <%15 iken güvenilir kategorik H2 geçişi veya
etkili oran ≥%25 iken hiçbir nöral/davranışsal A kayması olmaması.

## P5 — H3 ana öngörüsü

A engramını susturmanın mutlak etkisi A ton desteğinde öndeyken, A gerideyken
olduğundan büyüktür. `strength=1`, etkili %25 erişim, tam tag-test eşleşmesi:

- A önde: `ΔE ≈ -0,54` (`ΔNCI ≈ -0,56`),
- A geride: `ΔE ≈ +0,05` (`ΔNCI ≈ +0,09`).

Öngörü kategorik flip değil, **konuma bağlı etki büyüklüğü asimetrisidir**.

Çürütücü gözlem: aynı etkili erişim ve ton yanlılığı altında gerideki-A
susturma etkisinin mutlak büyüklüğü öndeki-A etkisine eşit ya da daha büyük.

## P6 — hücresel örtüşme bir moderatördür

Aynı dondurulmuş çekirdekte `%8` seyreklik ve `strength=1` için H1 kanıt kaybı:

- örtüşme `%10–%20`: `ΔE ≈ -0,20`,
- `%30`: `≈ -0,37`,
- `%40`: `≈ -0,53`,
- `%50`: `≈ -0,61`,
- `%60`: `≈ -0,72` ve 5/5 ağda A → mixed.

H3 başlangıç ayrışması seçilen ton ölçeğinde sıfır örtüşmede kurulmaz; `%10–%60`
örtüşmede kurulur ve `|öndeki ΔE|−|gerideki ΔE|` pozitiftir (ızgara minimumu
yaklaşık 0,27).

Çürütücü gözlem: eşit etkili erişimde yüksek-örtüşmeli hayvanların H1 nöral
zayıflaması düşük-örtüşmelilerden sistematik olarak daha küçükse veya H3
asimetri yönü tersine dönüyorsa bu moderasyon öngörüsü reddedilir.

## P7 — davranış ve güç analizi sınırı

NCI çekici kimliğini; `E=A_özgün-B_özgün` ise mutlak imzalı geri-getirme
kanıtını verir. Davranış zarfı `E` üzerinden kurulsa da kazma ayrım oranıyla
özdeş değildir. `β` ve hayvan-içi varyans pilotta ölçülmeden tek bir
davranışsal büyüklük veya Cohen `dz` öngörülmez. Şu anki yapısal-tohum `dz`
değerleri güç analizinde kullanılamaz.

Kalibrasyon şartı: pilot `E`-benzeri nöral ölçüm ile davranış arasında monoton
bir ilişki göstermiyorsa lojistik okuma modeli değiştirilmelidir.
