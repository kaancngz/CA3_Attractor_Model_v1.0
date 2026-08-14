# 00 — Projeyi nasıl anladım

Tarih: 2026-08-13
Kaynak: `README.md` (OneDrive'daki asıl dosyadan kopyalandı; asıl dosya yerinde duruyor)

Bu dosya README'nin özeti değil; **kendi cümlelerimle** ne yapacağımızı ve neyi henüz
bilmediğimi kayıt altına alıyor. Sorular §3'te.

---

## 1. İş ne

Yürütülmekte olan bir *in vivo* optogenetik deneyin hesaplamalı eşdeğerini kuruyoruz.
Deney dorsal CA3'te, RAM/DOX ile etiketlenmiş bir bağlam engramını ArchT ile susturuyor ya da
ChR2 ile sürüyor, ve hayvanın koku-kuyusu tercihinin nasıl kaydığına bakıyor. Burada hayvan yok,
kod var.

Sorulan asıl şey şu: **deneyin ulaşabildiği manipülasyon oranı, rekabetin sonucunu çevirmeye
yeter mi?** Çünkü gerçekte manipüle edilen hücre oranı üç çarpanın çarpımı — etiketleme verimi,
fiber ışık konisinin eriştiği hacim oranı, ve A/B örüntülerinin örtüşme oranı — ve bu çarpım
küçük bir sayı. Çekici ağlarda etki doğrusal olmadığı için "küçük oran = küçük etki" çıkarımı
geçersiz: bir eşiğin altında hiçbir şey görülmez, üstünde ani geçiş olur. Eşiğin nerede
olduğunu sözle söyleyemezsin, hesaplaman gerekir. Projenin omurgası bu.

İkinci, bence daha kıymetli iş: bu hesaptan **mekanistik bir etki büyüklüğü** çıkarmak ve
güç analizindeki dz ≥ 1,2 varsayımının yerine koymak. O varsayım şu anda literatürden ödünç,
devrenin özelliklerinden türetilmemiş.

## 2. Neden zamanlaması önemli

Deneysel veri **henüz yok**. Model önce kurulur, öngörüleri tarihli olarak dondurulur, veri
sonra gelir. Bu gerçek bir sınama; veri geldikten sonra kurulan hiçbir model bunu sağlayamaz.
Bu avantajı kaybetmenin tek yolu öngörüleri geciktirmek. Yani `predictions/` erken yazılacak.

Buna bağlı olarak parametreler asla modelin ürettiği sonuçtan türetilmeyecek: ya literatürden
(referansıyla, okunarak), ya pilottan (gelene kadar `null` ve taranan), ya da açıkça serbest.
Kaynağı olmayan sayı yazılmayacak.

## 3. Modelin üretmesi gereken şey

Ham çekici örtüşmesi değil. İki çıktı:

1. **Ayrım oranı**, [−1, +1] ölçeğinde — deneyin birincil davranışsal ölçütüyle aynı ölçek.
   Aksi hâlde karşılaştırma yapılamaz.
2. **Reaktivasyon oranı** (etiketli set ∩ test-anı etkin set) / etiketli set, ve bunun
   **şans düzeyi** karşılığı. Bu, davranıştan bağımsız ikinci bir kalibrasyon kancası;
   modelin en sağlam sınama noktası bence bu, çünkü davranışa göre çok daha az serbestlik var.

Ayrıca hem etki hem de varyans **hayvan-içi** (dz) hesaplanmalı — deney ışık AÇIK/KAPALI'yı
aynı hayvanda karşılaştırıyor. Sanal kohort karşı-dengelemeyi de taklit etmeli.

## 4. Katmanlar

- **Katman 0 — oran temelli rekabet + ortak inhibisyon.** Faz portresi ve bifurkasyon burada.
  Kademeli-mi-eşikli sorusunun ilk cevabı, ipucu→tercih eşlemesi burada çıkar. Atlanmayacak.
- **Katman 1 — seyrek ikili çekici ağ.** Asıl cevap burada üretilecek, çünkü "etiketli
  hücrelerin %15'ini sustur" işlemi ancak burada birebir yapılabilir; örtüşme oranı, etiketleme
  verimi ve reaktivasyon oranı doğal karşılıklarını burada bulur.
- **Katman 2 — spiking.** Yalnızca ışığın zaman yapısı (20 Hz, 15 ms, sürekli vs darbeli,
  deneme-öncesi başlama) modellenmek istenirse. Şimdilik koşullu.

## 5. Modelin YAPAMAYACAĞI şey — en kritik madde

Model hipotezi doğrulamaz. Çekici ağlar yeterince esnektir; parametreleri uygun seçersen hemen
her sonucu üretirler. "Model beklediğimi verdi" bir kanıt değil, olsa olsa tutarlılık kontrolü.

Asıl risk döngüsellik: parametreleri beklenen davranışsal sonuca göre ayarlarsak öngörmüş
olmayız, uydurmuş oluruz. Buna karşı iki savunma var ve ikisi de bu projede uygulanabilir:
zamanlama (veri henüz yok) ve provenance (parametreler bağımsız kaynaklardan). Bunlar
prosedürel; gevşetilirse proje bilimsel değerini kaybeder, çalışmaz hâle gelmez — tehlike bu.

Deney negatif çıkarsa model yanlışlanmış olmaz. Model "bu etki büyüklüğü zaten ölçülemezdi"
diyorsa, bu negatif sonucun *yorumu* olur. Muhtemel en gerçek katkı bu.

Kapsam dışı olduğunu not ediyorum: biyofiziksel mikrodevre rekonstrüksiyonu, derin öğrenme /
vekil model, Hopfield-Transformer denklik hattı (ayrı iş, bu depoya girmeyecek), veriye
kalibrasyon (öngörüler donduktan sonra ayrı aşama), CA1/DG ağları.

---

## 6. Belirsiz bulduklarım — soruldu, cevap bekliyor

Bunların hiçbirini varsayımla doldurmadım.

1. **H3'ün çift disosiyasyonu nasıl elde ediliyor?** §1.4'e göre yalnızca bağlam A etiketleniyor.
   "Etiketli anı hâlihazırda gerideyken susturma" koşulunun, ton-yüksek bağlamın hayvanlar arası
   karşı-dengelenmesinden geldiğini varsayıyorum (bazı hayvanda A ton-yüksek, bazısında
   ton-düşük). Sanal kohortun yapısı buna bağlı.
2. **Bağlam C testinde ton açık mı?** Tüm C prob denemelerinde sürekli mi, yoksa ton-VAR/ton-YOK
   aynı hayvan içinde karşı-dengeleniyor mu? Okuma koşullarının yapısı buna bağlı.
3. **C'de ayrım oranının pozitif kutbu ne?** C'de "doğru kuyu" tanımlı değil. Ölçüt
   "ton-yüksek bağlamın ödüllü kokusu" mu? Tanım olmadan §1.7 okuması yazılamaz.
4. **Grup 2'de (ChR2, bağlam B) ton durumu ne?** B ton-düşükse aktivasyon yanlılıkla aynı yöne
   iter, ton-yüksekse karşı yöne. İki farklı öngörü çıkar.
5. **Ton yanlılığı modelde nasıl doğuyor?** Önerim: ton girdisinin her örüntüye ağırlığı,
   eğitim boyunca birlikte-görülme olasılığıyla (0,65/0,35) orantılı olarak Hebbian biçimde
   oluşuyor. Onay bekliyor.
6. **Işık konisi:** kapsanan hücre oranı literatür zayıflama uzunluğundan hesaplanacak mı,
   yoksa taranan serbest parametre mi kalacak? README ikisini de ima ediyor.
7. **Pilot 2'nin ölçtüğü örtüşme neyin örtüşmesi?** Etkin toplulukların örtüşmesi mi
   (ör. catFISH / RAM+c-Fos), yoksa depolanmış örüntülerin mi? Modeldeki `overlap`
   parametresinin karşılığı buna göre değişir; ikisi aynı şey değil.

## 7. Sorulmadan söylenmesi gereken iki şey

- **dz tek bir sayı olarak üretilemez.** Hayvanlar-arası varyansın kaynakları (etiketleme
  verimi, örtüşme, ışık kapsaması dağılımları) henüz ölçülmedi. Model ancak
  "varsayılan varyans → dz" eşlemesi verebilir. §3.1'in çıktısını böyle çerçeveleyeceğim;
  tek bir dz yazmak §12'deki sayı uydurma yasağını çiğnemek olur.
- **Donanım:** README §10 "12 çekirdek, 15 GiB RAM" diyor. Bu makine 12 çekirdek ama
  **31,7 GB** RAM. Kısıt README'de yazandan gevşek.

## 8. Kurulum kararları (bu oturumda alındı)

- Depo yerel diskte: `C:\Dosyalarım\Lokal projeler\CA3 engram rekabeti` (git init edildi).
  Gerekçe: OneDrive'ın `.git` ve `.venv` senkronlaması çakışma ve yavaşlık üretir.
  README'nin OneDrive'daki asıl kopyası yerinde bırakıldı, buraya kopyalandı.
- Bu oturumun kapsamı yalnızca bu not. Klasör iskeleti, `params/` ve Katman 0 sonraki adım.
