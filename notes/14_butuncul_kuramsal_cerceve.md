# Bütüncül kuramsal çerçeve ve deney–model eşleme sözleşmesi

Tarih: 2026-08-15

## 1. Karar

Birincil ve v1.0 kapsamında tek teorik model,
`models/ca3_sparse_attractor/` altındaki seyrek hücre-düzeyi otoasosiyatif
çekirdektir. H1-H3 öngörüleri yalnız bu dondurulmuş mimariden alınır.

## 2. Beş katmanlı eşleme

### Katman 1 — Eğitim istatistiği → öğrenilmiş destek

Deneyde `%65/%35`, iki test akımının şiddeti değildir. Aynı tonun iki bağlamda
görülme olasılığıdır. Eşit A/B öncülleri altında ton varken:

`λ_A = P(A|ton) = P(ton|A) / [P(ton|A)+P(ton|B)]`

Dolayısıyla `%65/%35` programında `λ_A=0,65`, `λ_B=0,35` olur. Bu, hayvanın
Bayes algoritması çalıştırdığı iddiası değil; öğrenilmiş birlikte-görülme
istatistiğinin normalize edilmiş indirgenmiş temsilidir. Hipokampal
temsillerin deneme-deneme uyaran–sonuç geçiş olasılıklarıyla güncellenebildiği
hesaplamalı birincil çalışma Boorman ve arkadaşlarında gösterilmiştir
([DOI](https://doi.org/10.1016/j.neuron.2016.02.014)).

Ton yokluğu için iki rakip ve önceden ayrılmış model vardır:

1. `full_contingency`: yokluk da öğrenildiyse destek tersine döner (`0,35/0,65`).
2. `presence_only`: yokluk kullanılmıyorsa destek nötrdür (`0,50/0,50`).

P4 bu iki modelin deneysel karşılaştırmasıdır; yokluğun bilgi taşıdığı
varsayılmamıştır.

### Katman 2 — Öğrenilmiş destek → CA3 afferent ipucu

Tek fiziksel ton için toplam afferent hedef bütçesi sabittir. `λ`, bu sabit
bütçenin A ve B projeksiyonlarına ayrılan payıdır. Örneğin 20 hedef slotunda
`λ=0,65`, yaklaşık 13 A ve 7 B hedefi demektir. Fiziksel cue gücü ayrı bir
değişkendir. Böylece eğitim olasılığı, akım şiddeti ve toplam girdi enerjisi
birbirine karışmaz.

İlk yanlış uygulamada A ve B'ye eşit sayıda hücre üzerinden farklı genlik
verilmişti. İkili nöronlarda iki genlik de eşik üstündeyse 65/35 farkı ilk
adımda siliniyordu. Sabit-hedef-bütçesi kodu bu temsil hatasını giderdi.

### Katman 3 — CA3 çekici dinamiği

İki bellek, tam hücre kimliği bilinen seyrek ikili örüntülerdir. Rekürren alan,
standart merkezlenmiş Hebbian/covariance kuralıdır:

`W_ij ∝ Σ_μ (ξ_i^μ-a)(ξ_j^μ-a)`

Kod, öz-bağlantıları sıfırlanmış (`W_ii=0`) yoğun `W` matrisini kurmadan aynı
alanı örüntü örtüşmeleri üzerinden tam eşdeğer biçimde hesaplar. Bu eşdeğerlik
birim testinde yoğun matris hesabına karşı sayısal olarak doğrulanır. Formalizm,
örtüşen seyrek engramlar için
Gastaldi ve arkadaşlarının kullandığı standart çekici tanımı ve benzerlik
ölçüsüyle uyumludur ([DOI](https://doi.org/10.1371/journal.pcbi.1009691)).

CA3 rekürren sinapslarının örüntü tamamlama için biyolojik ve hesaplamalı
dayanakları; CA3'te bozulmuş girdiden koherent örüntü geri getirmeyi gösteren
Neunuebel ve Knierim ([DOI](https://doi.org/10.1016/j.neuron.2013.11.017)),
seyrek CA3 rekürren bağların gerçek-ölçek modelde örüntü tamamlamasını gösteren
Guzman ve arkadaşları ([DOI](https://doi.org/10.1126/science.aaf1836)) ve
CA3-CA3'te geniş/simetrik STDP'yi ölçen Mishra ve arkadaşlarıdır
([DOI](https://doi.org/10.1038/ncomms11552)).

Hızlı global inhibisyon, etkin hücre sayısını engram seyreklik düzeyinde tutan
bir etkinlik tavanıyla indirgenmiştir. Bu bir interneuron mikrodevresi iddiası
değildir; çekici rekabetinin minimal teorik kısıtıdır.

### Katman 4 — RAM ve ışık erişimi

Dört işlem ayrı tutulur:

1. çıplak-A'da etkin erken temsil,
2. bu temsil ile testteki nihai A engramının uyuşma oranı,
3. RAM etiketleme verimi,
4. etiketlilerin fiber/ışık tarafından erişilebilen oranı.

RAM, etkin toplulukları hassas ve zamansal kontrollü biçimde işaretlemek için
geliştirilmiştir; fakat “etiketli hücre = testteki tam engram” eşitliği sistemin
özelliği değildir ([Sørensen et al., 2016](https://doi.org/10.7554/eLife.13918)).

Modelde etkili erişim:

`|ışıkla erişilen etiket ∩ nihai A| / |nihai A|`

olarak doğrudan sayılır. Nominal etiket oranı bunun yerine kullanılmaz.

### Katman 5 — Nöral durum → davranış

Çekici kimliği okuması:

`NCI = (A_özgün - B_özgün) / (A_özgün + B_özgün)`

NCI, kazananın kimliğini verir; fakat mutlak geri-getirme gücünü siler. Örneğin
`A_özgün=0,2, B_özgün=0` ve `A_özgün=1, B_özgün=0` için NCI aynıdır. Bu nedenle
ayrıca imzalı geri-getirme kanıtı tanımlanır:

`E = A_özgün - B_özgün`

Davranışsal kazma ayrım oranı bunların hiçbiriyle özdeş değildir. Beklenen ikili
tercih için `E` üzerinde ayrı bir lojistik ölçüm modeli kullanılır:

`E[DR] = tanh[(β·E+b)/2]`

`β` ve `b` pilot davranış verisi olmadan bilinmez. Bu nedenle model şimdilik
yön, sıralama, eşik ve `β` duyarlılık zarfı üretir; tek bir davranışsal DR veya
güç analizine girecek `dz` uydurmaz.

## 3. Bağlamların tam model karşılığı

Deney | Model
--- | ---
A testi | A'ya özgü sürekli bağlam alanı
B testi | B'ye özgü sürekli bağlam alanı
C + ton | A/B bağlam alanı yok; yalnız tonun öğrenilmiş `λ` desteği
C + ton yok | `full_contingency` veya `presence_only` rakip modeli
ArchT | erişilen etiketli hücrelere negatif alan
ChR2 | erişilen etiketli hücrelere pozitif alan
Histolojik reaktivasyon | etkin etiket / toplam etiket; şans = etkin hücre oranı

Bağlam C için “sıfır girdi” denmez. Model yalnız A/B bellek altuzayını temsil
ettiği için C, **A/B'ye özgü bağlam kanıtının yokluğu**dur; ton alanı ve global
seyreklik dinamiği devam eder. Yeni bir C belleği/çekicisi eklenmemiştir.

## 4. Bağımsız geçerlik kapıları

H1-H3 görülmeden önce 2.400 hücre × 5 yapısal tohumda şu 10 kapı uygulandı:

1. sessiz dinlenim sabit noktası,
2. A sabit noktası,
3. B sabit noktası,
4. %20 A ipucundan tam A örüntü tamamlama,
5. %20 B ipucundan tam B örüntü tamamlama,
6. %5 A ipucunun yanlış hatırlama başlatmaması,
7. %5 B ipucunun yanlış hatırlama başlatmaması,
8. %5 hücrelik rakip perturbasyondan A'ya dönüş,
9. aynı kontrolün B yönü,
10. A/B simetrisi.

Eşik `0,08–0,16` boyunca 5/5 ağ ve 50/50 kapı geçti. `0,18` noktasında kısmi
ipucundan tamamlama kayboldu. Dondurulan `0,12`, geçerli platonun orta
noktasıdır; H1-H3 çıktısına göre seçilmedi.

## 5. Şu anki kuramsal sonuçlar

### λ havzası

- `λ=0,65`: 5/5 A,
- `λ=0,35`: 5/5 B,
- `λ=0,50`: simetrik sınır; sonucu yalnız tohum/tie-break belirliyor,
- daha güçlü cue, uçlardaki yönü değiştirmiyor; sınır çevresinde marjı dereceli
  hâle getiriyor.

Bu, `%65/%35` eğitim programının **öğrenilmiş destek gerçekten bu oranı
yansıtırsa** doğru çekiciyi seçmeye yeterli olduğunu öngörür.

### H1 — gereklilik

Varsayılan RAM×fiber tavanında nihai A'nın en fazla %25'ine erişildi. Bu
aralıkta, susturma gücü 0,25'ten 4 model birimine çıkarılsa bile A bağlamındaki
çekici **kimliği** 5/5 ağda A kaldı; fakat anı etkinliği kayıpsız değildi.
Etkili %25 erişimde:

- `strength=1`: A-engram etkinliği yaklaşık 0,20, etiketli reaktivasyon 0,40 ve
  imzalı geri-getirme kanıtı 0,20 azaldı (`E: 1,00 → 0,80`),
- `strength=4`: sırasıyla yaklaşık 0,25, 0,50 ve 0,25 azaldı
  (`E: 1,00 → 0,75`).

Davranış zarfı bu nedenle zayıflar, fakat şansa çökmez. Örneğin `strength=4`
için beklenen DR, serbest `β=1` altında 0,46'dan 0,36'ya; `β=4` altında
0,96'dan 0,91'e iner. Bunlar deneysel DR iddiası değil, ölçüm-modeli
duyarlılığıdır.

Bu H1'i “yanlış” ilan etmez; koşullu ve güçlü bir ayrım üretir: etkili erişim
%25'in altında kalırsa klasik dağıtık çekici, **kısmi reaktivasyon/güven kaybı**
öngörür ama çekici kimliğinin veya seçimin şansa çökmesini öngörmez. Deney şansa
yakın güçlü H1 etkisi bulursa en az biri gerekir: gerçek etkili erişim daha
yüksek, ışık ağ düzeyinde dolaylı yayılıyor, etiketli hücreler rastgele değil
çekirdek/hub hücreler veya davranış okuması küçük nöral kayba çok hassas.

### H2 — yeterlilik

Nihai A'ya etkili erişim yaklaşık %20'de tohum-bağımlı geçiş, %25'te 5/5 A
çekicisine dönüş üretti. Tag-test uyuşması %75 olduğunda nominal %25 erişim
etkili yaklaşık %18'e indi ve yalnız 2/5 ağ döndü; uyuşma %50 olduğunda etkili
yaklaşık %12 ile 0/5 döndü.

Ana değişken nominal viral etiket değil, `erişilen etiket ∩ nihai A` oranıdır.

### H3 — konuma bağlı asimetri

Susturma, A öndeyken imzalı kanıtı B yönüne dereceli kaydırdı; A zaten gerideyken
etki çok küçüktü. `strength=1`, %100 tag-test eşleşmesi ve etkili %25 erişimde:

- A önde: ortalama `ΔE ≈ -0,54` (`ΔNCI ≈ -0,56`),
- A geride: ortalama `ΔE ≈ +0,05` (`ΔNCI ≈ +0,09`; küçük; A etiketi içindeki ortak A∩B
  hücrelerinin susturulması B desteğini de bir miktar azaltıyor),
- iki durumda da 5/5 kategorik çekici kimliği korunuyor.

Dolayısıyla mevcut modelin H3 öngörüsü “mutlaka rakip anıya tam flip” değil;
**öndeki anıyı susturmanın kanıt etkisi, gerideki anıyı susturmaktan çok daha
büyüktür.** Davranışsal seçimde flip olup olmaması `β` ölçüm modeline bağlıdır.

## 6. Dondurulmuş çekirdek sağlamlık taraması

Mimari ve `threshold=0,12` değiştirilmeden 5 engram seyreklik düzeyi
(`%4–%12`) × 7 A/B örtüşmesi (`%0–%60`) × 5 yapısal tohum, toplam 175 ağ
tarandı.

- Bütün 35 hücrede 5/5 tohum bağımsız 10 çekici kapısının tamamını geçti.
- `%8` seyreklikte H1 `ΔE`, örtüşme `%10–%20` iken yaklaşık `-0,20`; `%30,
  %40, %50, %60` iken sırasıyla yaklaşık `-0,37, -0,53, -0,61, -0,72` oldu.
  `%60` örtüşmede H1 sonrası 5/5 ağ A'dan **mixed** duruma geçti.
- H2, bütün ızgarada 4/5 veya 5/5 A seçimi üretti.
- Örtüşme sıfırken seçilen `tone_scale=0,5` altında 65/35 ve 35/65 ipuçları
  saf A/B çekicilerini seçmedi; bu nedenle H3 o sütunda tanımsızdır. Örtüşme
  `%10–%60` olduğunda H3 başlangıç koşulu bütün tohumlarda geçti ve
  `|öndeki ΔE|−|gerideki ΔE|` her hücrede pozitifti (en küçük yaklaşık 0,27).

Sonuç: `%8` seyreklik ve `%20` örtüşme tek bir ince ayarlı ada değildir. Fakat
**örtüşme, H1'in büyüklüğü ve H3'ün kurulabilmesi için nedensel moderatördür**;
pilot histolojide ölçülmesi gereken başlıca parametrelerden biridir. Bu tarama
H1-H3'e göre mimari değiştirmedi; aynı dondurulmuş çekirdeğin dış-geçerlik
kontrolüdür.

Çıktı:
`outputs/ca3_sparse_attractor/robustness_overlap_sparsity_v1.json`.

## 7. Yanlışlanabilirlik sözleşmesi

Gözlem | Yanlışlanan halka
--- | ---
Pilot davranışta 65/35 ton yönü sistematik olarak tahmin etmiyor | eğitim istatistiği → öğrenilmiş destek
Hücre reaktivasyonu A/B çekici yönüyle uyuşmuyor | CA3 çekici veya nöral okuma
Etkili erişim < %15 iken H2'de güçlü/kategorik A geçişi | rastgele-altküme manipülasyon varsayımı
Etkili erişim ≤ %25 iken H1'de çekici kimliğinin/tercihin şansa çökmesi | klasik dağıtık örüntü tamamlama, rastgele-hedef varsayımı veya davranış okuması
H3'te gerideki-A susturma etkisi öndeki-A'dan eşit/büyük | konuma bağlı çekici asimetrisi
Ton yokluğu nötr kalırken `full_contingency` öngörüsü | yokluğun öğrenildiği model
Ton yokluğu ters tercih üretirken `presence_only` öngörüsü | yokluğun bilgi taşımadığı model

## 8. Literatür sentezi ve sınır

- Wills ve arkadaşlarının ani/popülasyon düzeyinde çekici geçişleri, çekici
  dinamiğinin deneysel imzasına dayanak verir
  ([DOI](https://doi.org/10.1126/science.1108905)).
- Neunuebel–Knierim ve Guzman çalışmaları CA3 örüntü tamamlama/rekürrens
  bağını doğrudan destekler.
- Mishra çalışması CA3-CA3 için simetrik Hebbian plastisiteyi destekler.
- Gastaldi çalışması seyrek ve örtüşen ikili engramların standart formalizmini
  sağlar ve fazla örtüşmenin engramları birleştirebileceğini gösterir.
- Delamare, Tomé ve Clopath'ın güncel modeli inhibisyon, eksitabilite ve
  engram örtüşmesinin birlikte ele alınabileceğini gösterir; fakat odağı bellek
  **oluşumu/bağlanmasıdır**, bizim test-sırası H1-H3 manipülasyonumuz değil
  ([DOI](https://doi.org/10.1523/JNEUROSCI.0846-23.2024)).
- Kim ve arkadaşlarının seçici inhibisyon modeli güçlü rekabet için olası bir
  mekanizma sunar; mekanizmanın E→I heterosynaptik plastisite kısmı deneysel
  olarak doğrulanmış değildir ve bu projede aktif çekirdeğe eklenmemiştir
  ([DOI](https://doi.org/10.1371/journal.pcbi.1013267)).

## 9. Kalan ama artık yerli yerinde duran bilinmeyenler

Model kuramsal olarak test edilebilir durumdadır; biyolojik olarak tekil sayısal
öngörü için şu pilot değerleri hâlâ gereklidir:

- gerçek A/B hücresel örtüşmesi,
- çıplak-A/test-A eşleşmesi,
- RAM verimi,
- fiberin etkili erişimi,
- ton programının davranışta öğrenilmiş desteği,
- NCI→kazma ayrım oranı eğimi ve deneme/hayvan varyansı.

Bunlar model boşlukları değil, açık ölçüm kancalarıdır. Veri gelene kadar
tarama eksenidir; geldikten sonra öngörü dosyası değiştirilmeden parametreler
yerine konacaktır.
