# CA3 Engram Rekabeti — Hesaplamalı Model Projesi

**Sürüm:** `CA3_Attractor_Model_v1.0`

**Durum:** Veri-öncesi, dondurulmuş minimal CA3 attractor modeli

Bu depo yalnızca güncel seyrek CA3 attractor modelini, yeniden üretim
betiklerini, dondurulmuş öngörüleri ve bunlara ait sonuçları içerir. Eski
spiking prototipler ve üçüncü taraf referans kodları v1.0 kapsamına dahil
değildir.

> **Bu dosya ne için:** Bu depo, bir *in vivo* optogenetik deneyin hesaplamalı bir eşdeğerini kurar.
> Deney başka bir yerde (fiziksel laboratuvarda) yürütülüyor; burada kod var, hayvan yok.
> Bu README'yi okuyan ajan, projeyi sıfırdan anlayıp kurmaya başlayabilecek kadar bilgiye burada sahip olmalıdır.
> Eksik gördüğün bir şey varsa **uydurma, sor.**

---

## 0. Projenin kimliği ve sınırları

**Bu proje NE:** Hipokampus CA3 bölgesinde, örtüşen iki bağlamsal anının ortak bir geri getirme
ipucu için rekabetini modelleyen, çekici ağ (attractor network) temelli bağımsız bir hesaplamalı
çalışma. Kendi başına yayına gidebilecek bir iş olarak tasarlanıyor.

**Bu proje NE DEĞİL:**
- Bir doktora tezinin bölümü değil. Tezin deneysel kolu ayrı yürüyor; bu depo onun yerine geçmiyor,
  onu "doğrulamıyor", ona bağımlı da değil.
- Bir veri analizi projesi değil. Şu anda **hiç deneysel veri yok.** Deneyler 1-2 ay içinde
  başlayacak. Model, veri gelmeden önce öngörü üretmek üzere kuruluyor.
- Biyofiziksel ayrıntılı bir mikrodevre rekonstrüksiyonu değil. (Bkz. §9 Kapsam dışı.)

**Projenin bilimsel iddiası şu olacak:** Engram manipülasyonu deneylerinde gözlenen davranışsal
etkinin büyüklüğü, manipüle edilen hücre oranının doğrusal bir fonksiyonu değildir; rekabet halindeki
çekici dinamiği nedeniyle eşikli davranır. Bu, deneysel duyarlılığın sınırlarını belirler ve
literatürdeki "etki bulunamadı" sonuçlarının bir kısmı için mekanistik bir açıklama sunar.

---

## 1. Modellenen deneyin tam tanımı

Aşağıdaki ayrıntılar, yürütülen deneyin etik kurul dosyasından birebir alınmıştır. Modelin
kalibrasyonu ve çıktı ölçütleri bunlara uymak zorundadır — çünkü modelin öngörüleri bu deneyle
karşılaştırılacak.

### 1.1 Hayvan ve hedef bölge
- Fare (mouse), dorsal CA3, bilateral.
- Enjeksiyon koordinatları (bregma referanslı): AP −2,4 mm; ML ±2,3 mm; DV −2,1 mm.
- Optik fiber: 200 µm çekirdek çapı, NA 0,37; fiber ucu enjeksiyon koordinatının ~0,3 mm dorsalinde.
- **Modelleme açısından önemi:** Fiberin ışık konisi dorsal CA3'ün tamamını değil, sınırlı bir
  hacmini aydınlatır. Manipüle edilen hücre oranının üst sınırını bu geometri belirler. Bu, modelin
  ana kısıtlarından biri (bkz. §3.1).

### 1.2 Davranışsal görev (koku-bağlam ayrımı, kazma temelli)
- İki eğitim bağlamı (A ve B), her birinde solda ve sağda iki koku kuyusu.
- Kokular: nane ve karvon (pilotta nötrallik için sınanıyor). **Her iki koku her iki bağlamda da var.**
- **Görev kuralı:** Bağlam A'da nane kuyusunu kazmak şeker peletiyle ödüllendirilir; bağlam B'de
  kural terstir, karvon ödüllendirilir. Yani kokunun anlamı **yalnızca bağlam tarafından belirlenir.**
- Bağlam-koku eşleşmesi hayvanlar arasında karşı-dengelenir.
- **Kritik tasarım özelliği:** İki anı birbirine *denktir* — aynı yapı, aynı ödül, aynı duygusal
  değer, aynı deneme sayısı. Rekabet sorusu bu denklik üzerine kuruludur. Modelde de iki çekici
  simetrik kurulmalıdır; asimetri yalnızca ipucu istatistiğinden gelmelidir.
- Eğitim takvimi: Gün 1-4 bloklu (günde tek bağlam, 14-16 deneme, bağlam günden güne değişir);
  Gün 5-10 iç içe (aynı gün iki bağlam, aynı bağlamda ardışık en fazla iki deneme).
  Öğrenme ölçütü: >%90 doğruluk.
- Tek deneme: hayvan bariyer arkasında 10-20 s bekletilir (**optogenetik ışık bu dönemde başlar**),
  bariyer kalkar, en fazla 3 dakika. Doğru yanıt = önce ödüllü koku kuyusunu kazmak.
- Günlük seans 30-45 dk; bir hayvan günde tek seans.

### 1.3 Ortak işitsel ipucu — projenin özgün kısmı
- Eğitim sırasında her iki bağlamda **fiziksel olarak aynı** bir ton bulunur. İki bağlam arasındaki
  tek fark **tonun sunulma olasılığıdır.**
- Başlangıç olasılık programı: bir bağlamın denemelerinin ~%65'inde, diğerinin ~%35'inde ton var.
  Bu oran sabit değil, pilotta kalibre edilecek bir başlangıç değeri; gerekirse %80/%20'ye çekilecek.
- Ton, deneme içinde kısa bir olay-işareti değil; hayvan bağlamda olduğu sürece **kesintisiz** verilir.
  Yani ayrık bir uyaran değil, bağlamın kalıcı bir bileşeni olarak kodlanır.
- Ton, etiketleme penceresinde sunulmaz (etiketlenen topluluğun parçası olmaması için).
- Tonun hangi bağlamda yüksek olasılıklı olduğu hayvanlar arasında karşı-dengelenir.
- **Bu programın mantığı:** Tonun *varlığı* bir anıyı, *yokluğu* diğerini yordar. Böylece aynı
  hayvanda ölçülebilen, karşıt yönlü iki geri getirme koşulu elde edilir.
- Tonun yokluğunun yordayıcı olarak kullanılıp kullanılamadığı **varsayılmıyor**, pilotta ölçülüyor.
  Model bu soruya öngörü üretebilir (bkz. §5, P4).

### 1.4 Aktiviteye bağımlı etiketleme (RAM / DOX)
- Sistem: RAM (Robust Activity Marking), doksisiklin (DOX) ile kapatılır.
- Vektörler (AAV2/9, ≥5×10¹² vg/mL, hemisfer başına 0,3 µL, ~100 nL/dk):
  - `rAAV-RAM-d2TTA::TRE-ArchT-EGFP-WPRE-pA` — inhibitör opsin
  - `rAAV-RAM-d2TTA::TRE-hChR2(H134R)-EYFP` — eksitatör opsin
  - `AAV-RAM-d2tTA::TRE-EGFP-WPRE-bGH-polyA` — opsinsiz kontrol
- Etiketleme penceresi: DOX diyetten çıkarılır → hayvan **bağlam A'ya 10 dakika çıplak** (kuyu, koku,
  ödül yok) maruz bırakılır → hemen DOX'a geri döner. 24 saat sonra, DOX altında bağlam B'ye
  alıştırma (bu bağlam etiketlenmez). Sonraki tüm eğitim DOX altında.
- **Modelleme açısından kritik:** Etiketlenen popülasyon, bağlam A'nın *çıplak* temsilidir — koku ve
  ödül öğrenilmeden önceki hâli. Yani etiketli set, testte geri getirilen tam örüntünün bir
  altkümesi ve muhtemelen eksik bir örneklemidir. Model bunu iki ayrı kayıp olarak temsil etmeli:
  (a) etiketleme verimi < 1, (b) etiketlenen set ile test anındaki etkin set arasındaki kısmi uyum.

### 1.5 Optogenetik parametreler
- Aktivasyon: 473 nm, 15 ms puls, 20 Hz, ~%30 görev döngüsü, fiber ucunda 1-2 mW.
- İnhibisyon: 575 nm sürekli, fiber ucunda ~10 mW.
- Işık deneme-öncesi bekleme döneminde başlar, deneme boyunca sürer.
- Işık AÇIK/KAPALI mümkün olan her yerde **aynı hayvan içinde**, sırası karşı-dengelenerek.

### 1.6 Dört grup ve hipotezler
| Grup | Vektör | Test bağlamı | Manipülasyon | Hipotez |
|---|---|---|---|---|
| 1 | ArchT | A (etiketli) | A engramını sustur | H1 |
| 2 | ChR2 | B (etiketsiz) | A engramını etkinleştir | H2 |
| 3 | ArchT | C (hiç görülmemiş nötr) | ipucu zemininde etiketli engramı sustur | H3 |
| 4 | EGFP | (aynı koşullar) | ışık var, opsin yok | kontrol |

- **H1 (gereklilik):** Etiketli bağlamda engramın susturulması, bağlama özgü doğru kuyu tercihini
  ortadan kaldırır; tercih şans düzeyine geriler.
- **H2 (yeterlilik):** Hayvan etiketsiz bağlamdayken etiketli engramın etkinleştirilmesi, tercihi
  bulunduğu bağlamın kokusundan etiketli anının kokusuna kaydırır.
- **H3 (rekabet):** Ortak ipucu nötr bağlam C'de geri getirme ipucu olarak kullanıldığında tercih,
  ipucunun yüksek olasılıkla eşlik ettiği anı lehine yönelir. **Bu yanlılık zemininde** öne çıkan
  anının engramı susturulduğunda tercih rakip anı lehine kayar.
- H3'ün ince kısmı — ve modelin asıl hedefi: susturmanın etkisinin, etiketli anının *hâlihazırda
  öndeyken* büyük, *hâlihazırda gerideyken* belirgin biçimde küçük olması bekleniyor. Yani
  **susturma etkisi, rekabetteki mevcut konuma bağlı olarak asimetriktir.** Bu bir çift disosiyasyon
  öngörüsüdür ve doğrudan modellenebilir.
- Bağlam C: eliptik duvarlı, desenli kahverengi yüzeyli, 31 × 39 × 18 cm; hayvan bunu yalnızca
  test gününde görür. Yani C hiçbir çekiciye tam uymayan bir girdidir — sistemi rekabete zorlar.

### 1.7 Ölçütler (modelin ÜRETMESİ GEREKEN çıktı biçimi)
- **Birincil:** ayrım oranı = (doğru kuyuda kazı süresi − yanlış kuyuda kazı süresi) /
  (doğru kuyuda kazı süresi + yanlış kuyuda kazı süresi). 0 = tercih yok, negatif = ters tercih.
  **Model çıktısı bu ölçeğe dönüştürülmeli** — ham çekici örtüşmesi değil, [−1, +1] aralığında
  bir ayrım oranı üretmeli. Aksi hâlde deneyle karşılaştırılamaz.
- İkincil (kazma eğilimi/hızı): kuyu başına kazı yüzdesi, toplam kazı süresi, kazı yapılan deneme
  oranı, ilk kazıya gecikme, eğitim doğruluk eğrisi. Modelde bunların karşılığı yoktur; ama modelin
  öngördüğü etki türünü ayırt etmek için önemlidir — "anı seçimi değişti" ile "genel kazma eğilimi
  düştü" ayrımı deneyde bu ölçütlerle yapılıyor, modelde bu ayrım gürültü/kazanç parametresi
  üzerinden temsil edilebilir.
- Prob testleri ödülsüz, her biri 3 dakika; aynı hayvanda tekrarlı test yapılabiliyor.
- **Histolojik:** reaktivasyon oranı = (EGFP/EYFP⁺ ve c-Fos⁺ çift pozitif hücre sayısı) /
  (toplam EGFP/EYFP⁺ hücre sayısı). Bu, modelin doğrudan üretebileceği ikinci bir çıktıdır ve
  davranıştan bağımsız bir kalibrasyon kancasıdır — modelin en değerli sınama noktalarından biri.
  Gözlenen çift pozitiflik, etiketleme oranı × reaktivasyon oranı çarpımından hesaplanan **şans
  düzeyi örtüşme** ile karşılaştırılıyor. Model bu şans düzeyini de üretmeli.
- Dışlama: dorsal CA3'ün bilateral olarak %50'sinden azında viral ekspresyon → hayvan analiz dışı.

### 1.8 Örneklem ve güç
- Ana deney: 4 grup × n = 8-12 (üst uç 12) = 48 hayvan; iki pilot 8'er = 16; toplam en fazla 64.
- Güç varsayımı: hayvan-içi ışık AÇIK/KAPALI karşılaştırmasında n = 8, dz ≥ 1,2 için ~%80 güç;
  dz ≈ 1,0 için n ≈ 12 gerekiyor.
- **Bu projenin en somut katkı noktası:** dz ≥ 1,2 varsayımı literatürden ödünç alınmış, devrenin
  özelliklerinden türetilmemiş. Model, mekanistik bir etki büyüklüğü tahmini üretip bu varsayımın
  yerine geçebilir. (Bkz. §3.1 birincil soru.)

### 1.9 Pilotlarda ölçülecek, modele girdi olacak değerler
Bu değerler **henüz yok**; pilotlardan gelecek. Model bunları serbest parametre olarak taşımalı ve
değer geldiğinde sabitlenebilecek biçimde yazılmalı:
1. Dorsal CA3'te RAM etiketleme verimi (etiketli hücre / toplam hücre).
2. A ve B bağlam temsillerinin dorsal CA3'teki hücresel örtüşme oranı. **Bu, modelin ana
   parametresinin doğrudan deneysel ölçümüdür.**
3. Davranışsal ipucu yanlılığının büyüklüğü (%65/%35 programıyla elde edilen ayrım oranı kayması).
4. Nihai enjeksiyon hacmi ve fiber implantasyon derinliği.
5. Ton frekansı ve şiddeti.

---

## 2. Kuramsal çerçeve

CA3 piramidal nöronları aralarındaki yoğun rekürren bağlantılar sayesinde otoasosiyatif bir çekici
ağ gibi çalışır: eksik ya da belirsiz bir girdiden anının bütünü yeniden kurulur (örüntü tamamlama).
İki örüntü örtüşüyorsa, kısmi bir ipucu ikisini birden kısmen etkinleştirir ve kazanan, ortak
inhibisyon üzerinden çözülür.

Bu projenin çerçevesi tam olarak budur ve **yeni bir formalizm icat etmeyi gerektirmez.** Marr'dan
bu yana süren hipokampal çekici ağ kuramının içine, belirli bir deneysel manipülasyonu yerleştiriyor.
Ajanın işi yeni bir kuram kurmak değil; mevcut formalizmi bu deneyin ayrıntılarına indirmek.

Deneysel tasarımın model karşılıkları:

| Deneysel öğe | Model karşılığı |
|---|---|
| İki denk bağlamsal anı (A, B) | İki çekici örüntü, simetrik |
| Bağlamların paylaştığı özellikler | Örüntüler arası **örtüşme oranı** — ana serbest parametre |
| Olasılıklı ton (%65/%35) | Her iki örüntüye giden, farklı ağırlıklı ortak girdi |
| Bağlam C'de test | Hiçbir çekiciye tam uymayan girdi; rekabete zorlama |
| RAM etiketleme | Etkin popülasyondan **eksik ve gecikmeli** örneklem |
| ArchT susturma | Etiketli altkümenin bir kısmının etkinliğini bastırma |
| ChR2 aktivasyon | Aynı altkümeyi dıştan sürme |
| Fiber ışık konisi | Manipüle edilebilen hücre oranının geometrik üst sınırı |
| Ayrım oranı | İki çekiciye yakınlığın [−1, +1] ölçeğine okunması |
| Reaktivasyon oranı | Etiketli set ile test-anı etkin setin kesişimi / etiketli set |

---

## 3. Yanıtlanacak sorular

### 3.1 BİRİNCİL SORU (projenin omurgası)

> **Ulaşılabilir manipülasyon oranı, rekabetin sonucunu çevirmeye yeter mi; ve etki hangi biçimde
> beklenir?**

Gerekçe: etiketleme verimi × ışık konisinin erişebildiği hücre oranı × örtüşme oranı çarpımı,
gerçekte anı örüntüsünün yalnızca küçük bir kesrinin manipüle edildiği anlamına gelir. Çekici
ağlarda etki doğrusal değildir — bir eşiğin altında hiçbir şey görülmez, üstünde ani geçiş olur.
Bu soru sözle cevaplanamaz; hesaplanması gerekir.

Çıktı: manipüle edilen hücre oranı → beklenen ayrım oranı kayması eğrisi, eşik konumu ve eşiğin
etrafındaki duyarlılık bandı; ve buradan türetilmiş mekanistik bir etki büyüklüğü (Cohen dz eşdeğeri).

### 3.2 İKİNCİL SORULAR — modelin sözlü sezgiden AYRIŞTIĞI yerler

Model her yerde sezgiyle aynı şeyi söylüyorsa titizlik katar, içgörü katmaz. Değeri, ayrıştığı
yerlerde. Aday ayrışma noktaları:

1. **Kademeli mi eşikli mi?** Rekabet yalnızca inhibisyonla normalize ediliyorsa susturma oranı ile
   davranışsal kayma arasında yaklaşık doğrusal bir ilişki beklenir. Gerçek çekici dinamiği varsa
   sigmoid, hatta basamak beklenir. **Bu ikisi deneysel olarak ayırt edilebilir — ama ancak birden
   fazla ışık gücü denenirse.** Model bu tasarım kararını önceden söyler.
2. **ArchT ↔ ChR2 asimetrisi.** Sezgi ayna görüntüsü bekler. Çekici ağlarda bu zorunlu değil:
   çekici zaten doyduğu için sürmenin tavanı olabilir; ayrıca etiketli seti kendi doğal örüntü
   bağlamının dışında sürmek, örüntüyü tamamlamak yerine **bozabilir.** Model bu iki kolun niteliksel
   olarak farklı davranmasını mı öngörüyor? Dört gruplu tasarımda doğrudan sınanabilir.
3. **İpucu olasılığı → davranış eşlemesi.** İpucu %65/%35 ise tercih de %65/%35 mi olur, yoksa
   çekici dinamiği bunu kategorikleştirip uca mı çeker? Bu, ipucu istatistiğinden davranışa nicel
   bir eşlemedir ve tamamen modelden çıkar. Pilot 1 bunu ölçecek — yani **öngörü, veri gelmeden
   önce yazılabilir ve sonra sınanabilir.**
4. **Tonun yokluğu yordayıcı mıdır?** Deney bunu varsaymıyor, ölçüyor. Model, bir uyaranın
   *yokluğunun* çekici seçiminde kullanılabilir bir sinyal olup olmadığına dair öngörü üretebilir
   ve bu, olasılık oranına (%65/%35 vs %80/%20) bağlı olarak değişebilir.
5. **Örtüşme oranının kritik aralığı.** Örtüşme çok düşükse rekabet yoktur (iki bağımsız anı);
   çok yüksekse iki anı ayrışmaz (tek çekici). H3'ün sınanabilir olduğu bir **pencere** vardır.
   Model bu pencerenin sınırlarını verir; Pilot 2'de ölçülecek gerçek örtüşme oranı bu pencerenin
   içine düşüyor mu — deneyin yorumlanabilirliği doğrudan buna bağlı.
6. **Örneklem büyüklüğü karşılığı.** Her eşik eğrisi, bir hayvan-içi etki büyüklüğüne ve dolayısıyla
   bir n değerine çevrilebilir. Model, 8-12 bandının hangi senaryoda yeterli olduğunu söyleyebilir.

---

## 4. Ne YAPAMAZ — bu bölümü atlamak projeyi bitirir

**Model hipotezi doğrulamaz.** Çekici ağlar yeterince esnektir; parametreleri uygun seçersen hemen
her sonucu üretirler. "Model beklediğim sonucu verdi" bir kanıt değil, bir tutarlılık kontrolüdür.

**Asıl risk döngüsellik.** Parametreleri beklenen davranışsal sonuca göre ayarlarsan, öngörmüş
olmazsın, uydurmuş olursun. Kaçınmanın iki yolu — ikisi de bu projede uygulanabilir durumda:

1. **Zamanlama lehte.** Deneysel veri henüz YOK. Model önce kurulur, öngörüleri **yazılı olarak ve
   tarihli biçimde sabitlenir** (`predictions/` klasörü, §7). Veri sonra gelir. Bu gerçek bir
   sınamadır ve veri geldikten sonra kurulan bir model bunu asla sağlayamaz. **Bu projenin en büyük
   avantajı budur ve kaybedilmesi kolaydır — öngörüleri erken yaz.**
2. **Parametreler bağımsız kaynaklardan gelir.** CA3 rekürren bağlantı olasılığı, seyreklik, engram
   büyüklüğü oranları literatürden alınır; modelin ürettiği sonuçtan asla türetilmez. Her parametre
   `params/` altında **kaynağıyla birlikte** kayıtlı olmalı (bkz. §6 provenance kuralı).

**Model, deneyin yerine geçmez ve deneyin sonucunu belirlemez.** Deney negatif sonuç verirse model
yanlış olmaz; model "bu etki büyüklüğü zaten ölçülemezdi" diyorsa, bu negatif sonucun *yorumu* olur.
Bu, modelin en olası gerçek katkısıdır.

---

## 5. Dondurulmuş v1.0 mimarisi — seyrek ikili çekici ağ

Seyrek kodlu otoasosiyatif ağda örtüşen A/B örüntüleri **açıkça** tanımlıdır.
- Neden gerekli: (a) örtüşme oranı doğrudan bir parametreye çevrilir; (b) "A örüntüsünün
  hücrelerinin %15'ini sustur" işlemi **birebir** yapılabilir — ArchT'nin yaptığı şey soyutlanmadan
  modellenir; (c) etiketleme verimi, eksik örneklem olarak doğal biçimde temsil edilir;
  (d) reaktivasyon oranı ve şans düzeyi örtüşme doğrudan hesaplanabilir (§1.7).
- Birincil sorunun (§3.1) cevabı burada üretilir.
- Ölçek: numpy; birkaç bin nöron rahat.
- Öğrenme kuralı merkezlenmiş covariance-Hebbian biçimidir; öz-bağlantılar
  sıfırdır ve hızlı global inhibisyon seyrek etkinlik tavanıyla indirgenir.
- v1.0 milisaniye ölçeğinde spike veya optogenetik darbe treni üretmez;
  deneysel müdahaleleri etiketli hücrelere uygulanan pozitif/negatif alan
  olarak temsil eder.

---

## 6. Parametreler ve provenance kuralı

**Mutlak kural:** Hiçbir sayı koda gömülmez ve hiçbir sayı hafızadan yazılmaz. Her parametre
`params/*.yaml` içinde şu alanlarla durur:

```yaml
- name: ca3_recurrent_connection_probability
  value: null              # doldurulmadıysa null bırak, tahmin YAZMA
  unit: dimensionless
  source: literature       # literature | pilot | free | design
  reference: null          # DOI ya da tam atıf — "bilinen bir değer" demek yasak
  verified: false          # kaynak birebir okunup teyit edildi mi
  note: ""
```

`source` alanının anlamları:
- `design` — deneyin tasarımından gelen, kesin bilinen değer (ör. ton olasılığı %65/%35,
  ışık 20 Hz, 15 ms; §1'deki her şey). Bunlar bu README'den alınabilir.
- `literature` — yayından alınacak. **Referans zorunlu.** Kaynağı okumadan `verified: true` yazma.
- `pilot` — henüz ölçülmedi (§1.9). `value: null` kalır; model bunları serbest parametre olarak
  taramak zorundadır, tek bir varsayılan değere yapıştırmaz.
- `free` — modelin serbest parametresi; taranacak, kalibre edilmeyecek.

Literatürden sabitlenmesi gereken minimum küme: CA3 rekürren bağlantı olasılığı, CA3 piramidal
hücre sayısı (dorsal, tek hemisfer), aktivite seyrekliği, bağlamsal engram büyüklüğü oranı,
ArchT'nin ateşleme baskılama verimi, ChR2'nin sürme verimi, 575/473 nm ışığın beyin dokusundaki
zayıflama uzunluğu (ışık konisi hesabı için).

**Serbest parametre sayısını sayan bir kontrol yaz.** Model "her şeyi açıklayabilen" bir şeye
dönüşürse hiçbir şey öngörmez. Serbest parametre sayısı ve her birinin tarama aralığı, sonuç
dosyalarında raporlanmalı.

---

## 7. Öngörülerin sabitlenmesi (`predictions/`)

Bu projenin bilimsel değeri buradan geliyor. Kurallar:
1. Her öngörü kendi dosyasında, tarihli, değiştirilmemiş biçimde durur. Sonradan düzeltme yapılırsa
   **eski dosya silinmez**, yeni bir sürüm eklenir ve neyin değiştiği yazılır.
2. Her öngörü şu biçimde: hangi ölçüt (ayrım oranı / reaktivasyon oranı), hangi grup, hangi koşul,
   beklenen yön, beklenen büyüklük aralığı, ve **hangi gözlem bu öngörüyü çürütür.**
3. Çürütülemez öngörü yazma. "Etki görülebilir" bir öngörü değil.
4. Öngörüler Pilot 1 ve Pilot 2 verisi gelmeden önce tamamlanmalı — çünkü o veriler modelin girdisi
   olacak ve ondan sonra yazılan hiçbir öngörü bağımsız sayılmaz.

Minimum öngörü kümesi (§3.2'den): P1 kademeli/eşikli, P2 ArchT-ChR2 asimetrisi, P3 ipucu-tercih
eşlemesi, P4 tonun yokluğunun yordayıcılığı, P5 örtüşme oranının kritik penceresi, P6 gerekli n.

---

## 8. Doğrulama ve sağlamlık (atlanamaz)

- **Dejenerelik taraması.** Aynı davranışsal çıktıyı üreten kaç farklı parametre kümesi var?
  Tek bir "çalışan" parametre kümesi bulmak sonuç değildir.
- **Duyarlılık analizi.** Her parametrenin çıktı üzerindeki etkisi tek tek ve ikili etkileşimlerle.
- **Ablasyon.** Ortak inhibisyonu kaldır, rekürren bağlantıyı kaldır, örtüşmeyi sıfırla — model
  beklenen biçimde bozulmalı. Bozulmuyorsa o mekanizma sonucu üretmiyor demektir.
- **Şans düzeyi kontrolü.** Reaktivasyon oranı için model, deneyin kullandığı şans düzeyi
  hesabını (etiketleme oranı × reaktivasyon oranı) yeniden üretebilmeli. Üretemiyorsa model ile
  deneyin ölçüt tanımları uyuşmuyor — bu bir hata sinyalidir.
- **Tohum (seed) disiplini.** Her koşu tohumlu, her sonuç yeniden üretilebilir. Tohum ortalamaları
  ve tek koşu varyansı ayrı raporlanmalı — çünkü deneyde n = 8-12, yani tek hayvan varyansı önemli.
- **Hayvan-içi tasarımın taklidi.** Deney ışık AÇIK/KAPALI'yı aynı hayvan içinde karşılaştırıyor.
  Model de sanal hayvan başına eşleşmiş koşullar üretmeli ve etki büyüklüğünü **hayvan-içi**
  (dz) olarak hesaplamalı. Gruplar arası hesap yapılırsa güç analizi karşılaştırması geçersiz olur.
- **Karşı-dengeleme.** Deneyde bağlam-koku eşleşmesi, ton-bağlam ataması ve hangi bağlamın
  etiketlendiği hayvanlar arasında karşı-dengeleniyor. Sanal kohort da bunu yapmalı.

---

## 9. Kapsam dışı — yapılmayacaklar

- **Biyofiziksel ayrıntılı mikrodevre rekonstrüksiyonu.** Argümana bir şey katmaz, ayları yer.
- **Derin öğrenme / vekil model kurma.** Sorunun cevabı mekanizmada, uydurmada değil.
- **Hopfield-Transformer denklik argümanı.** Bu ayrı bir hat — temsil düzeyinde biçimsel bir denklik
  iddiası. Buradaki iş rekabet dinamiği. İkisini aynı çerçeveye sıkıştırırsan **ikisi de zayıflar.**
  Ayrı tut. Bu depoya sokma.
- **Deneysel veriye kalibrasyon (şimdilik).** Veri geldiğinde bu ayrı bir aşama olarak,
  öngörüler dondurulduktan sonra açılır.
- **CA1, DG ya da tam hipokampal devre modeli.** Hedef bölge dorsal CA3. DG girdisi ancak dıştan
  verilen bir örüntü olarak temsil edilir, ayrı bir ağ olarak modellenmez.

---

## 10. Teknik çerçeve

- Python 3.8.20 ve NumPy 1.20.1 ile doğrulandı; figür üretimi için
  Matplotlib 3.5.3 kullanılır.
- Model GPU veya spiking simülatörü gerektirmez.
- Dondurulmuş v1.0 depo yapısı:
```
models/ca3_sparse_attractor/          # birincil hücre-düzeyi teorik çekici modeli
apps/ca3_hypothesis_lab.html           # etkileşimli H1-H3 faz haritası ve mekanizma görünümü
params/ca3_sparse_attractor_v1.yaml
analysis/                              # güncel çıkarım ve figür betikleri
outputs/ca3_sparse_attractor/          # birincil geçerlik ve veri-öncesi öngörüler
predictions/                           # tarihli ve değiştirilmeyen veri-öncesi öngörüler
notes/                                 # güncel kararlar, doğrulama ve sonuç yorumu
```
- Kurulum:
  `python -m venv .venv` ve ardından
  `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Hızlı doğrulama:
  `.\.venv\Scripts\python.exe -m unittest discover -s models\ca3_sparse_attractor\tests -v`.
- Her figür yayın kalitesinde olmalı: eksen etiketleri birimli, örneklem sayısı belirtilmiş,
  gösterilen şeyin ne olduğu başlıktan anlaşılır. Eşik eğrisi figürü projenin ana figürü olacak.

---

## 11. Güncel durum ve sıradaki adım

1. Birincil teorik omurga `models/ca3_sparse_attractor/` altındaki seyrek
   hücre-düzeyi çekici modelidir. Eşik 0,08–0,16 bağımsız geçerlik platosunun
   orta noktası 0,12'de donduruldu; 2.400 hücre × 5 tohum 50/50 kapı geçti.
2. `%65/%35`, fiziksel akım değil öğrenilmiş normalize bağlam desteğidir;
   sabit toplam afferent hedef bütçesine çevrilir. Ton yokluğu için
   `full_contingency` ve `presence_only` rakip öngörüleri korunur.
3. RAM etiketi; çıplak-A/test-A eşleşmesi, etiketleme verimi ve fiber erişimi
   olarak üç ayrı kayıptır. Ana eksen nominal değil etkili nihai-A erişimidir.
4. İlk veri-öncesi H1-H3 öngörüleri
   `predictions/2026-08-15_sparse_attractor_v1_predata.md` içinde korunur.
   Birleşik 750-hücreli faz haritası ve açık çürütme kuralları
   `predictions/2026-08-15_joint_phase_map_v2_predata.md` içinde donduruldu.
5. Çekici kimliği (`NCI`), mutlak imzalı geri-getirme kanıtı
   (`E=A_özgün-B_özgün`) ve etiketli reaktivasyon ayrı tutulur; davranış
   duyarlılık zarfı mutlak kanıt üzerinden kurulur.
6. Aynı mimaride `%4–%12` seyreklik × `%0–%60` örtüşme × 5 tohum taraması
   tamamlandı: 175 ağın tamamı çekici kapılarını geçti. Örtüşme H1 büyüklüğü ve
   H3 asimetrisinin moderatörüdür; sonuç
   `outputs/ca3_sparse_attractor/robustness_overlap_sparsity_v1.json` içindedir.
7. `%0–%60` örtüşme × `%0–%50` etkili erişim × 5 manipülasyon gücü, aynı 25
   yapısal ağın eşleşmiş ışık-kapalı/açık koşullarında tarandı. Birincil
   noktada H1 kısmi nöral zayıflama, H2 kategorik A geçişi ve H3 pozisyonel
   asimetri üretir; H1 şansa çöküşü ve H3 tam B dönüşü üretmez.
8. Rekürrens, seyrek inhibisyon ve örtüşme ablasyonları tamamlandı. Rekürrens
   olmadan örüntü tamamlama; seyrek inhibisyon olmadan seçici H2; sıfır
   örtüşmede seçilen 65/35 rejimi altında H3 başlangıç rekabeti kurulmaz.
9. `apps/ca3_hypothesis_lab.html`, hesaplanan yüzeyleri etkileşimli gösterir;
   elle çizilmiş bir sonuç değil, JSON faz haritasının gömülü görünümüdür.
10. Deney eşlemeli recall–probe koşusu tamamlandı: 25/25 ağ A ve B'yi kısmi
   ipucundan tamamladı; 8 prob kolunda 400/400 kayıt ve bütün eşleşmiş ışık
   çiftleri üretildi. H2 B→A geçişi, H1 kısmi zayıflama ve H3 konumsal
   asimetri verdi; dört EGFP aynasında etki sıfırdı. Ayrıntı
   `notes/16_recall_probe_protocol_v1.md` içindedir.
11. Sıradaki bilimsel iş yeni mimari kurmak değildir. Pilot ölçümleri
   geldiğinde örtüşme, etkili erişim, ton desteği, manipülasyon gücü ve
   `E→ayrım oranı` eğimi kilitlenecek; ardından hayvan-içi varyansla gerçek
   `dz`/güç analizi yapılacaktır. Arka-plan bellek yükü aynı çekirdekte ikincil
   sağlamlık testi olarak kalır.
---

## 12. Çalışma kuralları

- **Sayı uydurma yasağı.** Kaynağı olmayan hiçbir sayı koda ya da metne girmez. Bilinmiyorsa `null`
  ve açık bir "bilinmiyor" notu. Bir değeri hatırlıyor gibi hissetmek, kaynak değildir.
- **Kaynak iki kez doğrulanır.** Bir literatür değerini yazmadan önce kaynağın kendisi okunur —
  arama sonucu özeti, ikincil aktarım ya da hatırlanan bir sayı yeterli değil.
- **Dil.** Kod ve kod içi yorumlar İngilizce; notlar ve rapor metinleri Türkçe. Terminoloji
  Türkçeleştirilirken İngilizce karşılığı parantezde verilir.
- **Ton.** Yumuşatıcı giriş cümlesi, örtük onaylama ve süsleme yok. Bir şey çalışmıyorsa çalışmıyor
  yazılır. Model beklenen sonucu vermiyorsa bu bir bulgudur, gizlenmez.
- **"Model hipotezi test ediyor" diye yazma.** Doğru ifade: hipotezi biçimlendiriyor, nicel öngörü
  üretiyor ve deneysel duyarlılığın sınırlarını belirliyor.
