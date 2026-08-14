# 02 — Kendi modelimiz: kararlar ve gerekçeleri

Tarih: 2026-08-13
Kod: `src/ca3/` — `params.py`, `engrams.py`, `network.py`, `readout.py`
Deneyler: `experiments/01_competition_smoke.py`, `experiments/02_find_working_regime.py`

## Ne aldık, nereden

- **Mimari ve dinamik:** Kim & Kim (2025). Izhikevich nöronları,
  AMPA/NMDA/GABA_A/GABA_B iletkenlikleri, yol başına doyan (tanh) akım sınırları,
  seçici inhibisyon mekanizması. Sayılar Tablo 1-2-3'ten ve not defterlerindeki
  `config` sınıfından; her biri `params.py` içinde kaynağıyla etiketli.
- **Ölçüt tanımları:** Feitosa Tomé ve ark. (2022, Nat Neurosci). Normalize ayrım
  indeksi, etiketlenen set ile testte etkin set ayrımı, reaktivasyon oranı.
  Kim & Kim'de bunların hiçbiri yoktu; bize RAM/DOX deneyine bağlanmayı bunlar
  veriyor.
- **Kendi kararlarımız:** `params.py` içinde `OURS` etiketli. Hepsi serbest
  parametre, hiçbiri ölçülmüş değer değil.

## Seçici inhibisyonu nasıl kurduk — en önemli karar

Kim & Kim'de seçicilik bir plastisite kuralı **değil**, bir seçilim etkisi:
kodlama sırasında inhibitör nöronlar önce ateşler ve uyarıcı hücrelerin çoğunu
susturur; hayatta kalanlar, o inhibitör kümeden az bağlantı alan hücrelerdir.
Engram bu hayatta kalanlardan oluşur — dolayısıyla kendi inhibitörleri onu
neredeyse hiç bastırmaz, rakiplerini bastırır.

Onlar bunu kodlama fazını simüle ederek elde ediyor; sonuçta ~10 hücrelik
engramlar ve örtüşme üzerinde hiç kontrol kalmıyor. Biz aynı ölçütü doğrudan
uyguluyoruz: I_k'dan en az inhibisyon alan hücreleri seçiyoruz. Mekanizma aynı,
engram boyutu ve örtüşme ise açık parametre.

`selective=False` yolu engramı rastgele seçer — bu **global inhibisyon kontrolü**:
inhibitör nöronlar kendi engramlarını da rakipleri kadar bastırır. Projenin ana
ablasyonu bu tek bayrak.

## Neden engramı büyüttük ve bunun bedeli

10 hücreyle *f* (susturulan kesir) ancak 0.1 adımlarla taranabilir; kritik kesir
ölçülemez. `engram_size = 100` yaptık.

Bedeli hemen çıktı: engramı 10 kat büyütünce her hücrenin aldığı rekürren
iletkenlik de 10 kat artıyor, tanh doyuma giriyor, uyarım inhibisyonu eziyor ve
**iki engram birden ateşliyor — rekabet hiç çözülmüyor.** Kim & Kim'in
iletkenlikleri kendi ~10 hücrelik engramları için ayarlanmış.

Çözüm: sinaps başına iletkenliği değil, **hücre başına toplam rekürren
iletkenliği** sabit tutmak (`normalize_recurrent`, `g_rc_target`). Bu bizim
kararımız, onlarda yok, ve serbest parametre olarak taranmak zorunda.

## Kalibrasyon — ve neden döngüsel değil

`g_rc_target` makaleden okunamaz. `experiments/02` ile tarandı ve **hipotezimizle
ilgisi olmayan** bir sayıya kalibre edildi: Kim & Kim'in bildirdiği "iki engrama
örtüşen bir ipucu denemelerin ~%80'inde birini geri getiriyor" oranı.

Bu meşru. Beklediğimiz ayrım kaymasına kalibre etmek olsaydı döngüsel olurdu.

**Ulaşılan: %45-55, hedef %80.** Fark kapanmadı; `q_max = 3 nS` tavanına
dayanıyoruz. Bu açık bir eksiklik, gizlenmiyor. Muhtemel çareler: EC sürüşünü
artırmak, gürültüyü artırmak, geri getirme penceresini uzatmak. Hiçbiri henüz
denenmedi.

## Modele girmeyen şeyler — bilerek

Fiber ışık konisi geometrisi, opsin kinetiği, mW, nm, viral titre, DOX zamanlaması.
Bunlar hayvana özel tesisat. Modelde kalan şey soyut işlem: *bir örüntünün f
kesrini kapat*. "Gerçekte hangi f'ye ulaşılabilir" deneycinin sorusu; model
f_kritik eğrisini verir, deneyci kendi f'sini o eğri üzerinde konumlandırır.

## Şu an çalışan üç şey

`experiments/01` çıktısı, koşul başına 30 deneme:

1. **Temiz ipucu doğru anıyı getiriyor ve yanlışını hiç getirmiyor.**
   ipucu=A → P(A)=0.50, P(B)=0.00. ipucu=B → P(B)=0.57, P(A)=0.00.
2. **İpucu yanlılığı → tercih eşlemesi tek yönlü ve düzgün.**
   yanlılık 0 → 1 arttıkça P(A) 0.00 → 0.13 → 0.37 → 0.47 → 0.50,
   P(B) 0.57 → 0.50 → 0.27 → 0.13 → 0.00. Kademeli görünüyor, eşikli değil —
   Kim & Kim'in Fig 12'deki doğrusal bulgusuyla aynı yönde.
3. **Susturma sonucu kaydırıyor.** Yansız ipucuyla, f arttıkça
   DI +0.082 → −0.344; P(A) 0.37 → 0.00; P(B) 0.27 → 0.50.

## Dikkat çeken ilk gözlem — henüz bulgu değil

f = 0.10 → 0.20 arasında geçiş dik: P(A) 0.30'dan 0.10'a düşerken P(B) 0.33'ten
0.50'ye çıkıyor. Eşik izlenimi veriyor ama **30 deneme bunu çözmez.** Daha ince f
adımları ve çok daha fazla deneme gerekiyor. Şu anda bir gözlem, iddia değil.

Ayrıca f arttıkça P(fail) 0.37'den 0.77'ye çıkıyor. Bu kendi başına bir öngörü:
susturma yalnızca tercihi kaydırmıyor, geri getirmeyi topyekûn bozuyor. Deneydeki
"anı seçimi değişti" ile "genel kazma eğilimi düştü" ayrımının model karşılığı bu.

## Hız

120 ms'lik geri getirme: **29 ms**. Referans uygulamada aynı ağ 79 saniye
sürüyordu — **~2700 kat**. Taramalar artık dakikalar mertebesinde.

## Yapılmayanlar

- STDP ile gerçek kodlama (şu an öğrenilmiş ağırlıklar doğrudan yazılıyor)
- Olasılıklı ton eğitimi (%65/35) — H3'ün yanlılık kaynağı
- DG ve CA1 katmanları
- Duyarlılık ve dejenerelik taraması (README §8)
- Kim & Kim Fig 8H / Fig 12'nin çoğaltılması
