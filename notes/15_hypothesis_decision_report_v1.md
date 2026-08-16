# H1–H3 birleşik faz haritası — veri-öncesi karar raporu v1

Tarih: 2026-08-15
Durum: deney/pilot verisi görülmeden dondurulmuş koşullu rapor

Bu rapor yeni bir mimari seçmez. Bağımsız doğrulanmış seyrek CA3 çekirdeğini
`örtüşme × etkili erişim × manipülasyon gücü` uzayında sınar. Yapısal
tohumlar hayvan varyansı veya p-değeri değildir.

## Birincil veri-öncesi nokta

- A/B örtüşmesi: `%20`
- etkili nihai-A erişimi: `%25`
- manipülasyon gücü: `1,0` model birimi
- 25 bağımsız yapısal ağ

### H1

- Ortalama `ΔE = -0.24`.
- Ortalama etiketli reaktivasyon değişimi `-0.23`.
- A dışına çıkan ağ oranı `4%`; şansa-yakın kanıt oranı `0%`.
- Karar: minimal nöral gereklilik desteklenir; özgün güçlü 'şansa çöküş'
  bu noktada desteklenmez.

### H2

- Ortalama `ΔE = 1.61`; A çekicisine geçen ağ oranı `100%`.
- Karar: yeterlilik hipotezi bu noktada desteklenir.
- `%20` örtüşme ve güç `1,0` için güvenilir A geçiş eşiği yaklaşık `22.5%`.

### H3

- Başlangıç A-önde/B-geride ayrışması: `100%` ağda geçerli.
- İmzalı konum etkileşimi `I = ΔE_önde−ΔE_geride = -0.60`.
- Pozisyonel asimetriyi gösteren ağ oranı `100%`.
- Rakip B'ye tam kategorik geçiş `0%`.
- Karar: konuma bağlı asimetri desteklenir; özgün güçlü 'rakibe tam
  dönüş' bu noktada desteklenmez.

## Varsayılan kesitte eşikler

Ölçüt | Etkili erişim eşiği
--- | ---:
H1: ağların çoğunda A dışına çıkış | `50.0%`
H1: ağların çoğunda şansa-yakın kanıt | `>50%`
H2: ≥%80 ağda A çekicisi | `22.5%`
H3: sağlam konumsal asimetri | `5.0%`
H3: ≥%80 ağda rakip B'ye tam geçiş | `>50%`

## Deneysel karar kuralları

1. H1'de `%20` civarı örtüşme ve `%25` etkili erişimde şansa yakın güçlü
   çöküş bulunursa, rastgele-dağıtık etiket varsayımı reddedilir; hub/çekirdek
   hücre seçiciliği veya ağ-yayılımlı optogenetik etki gerekir.
2. H2'de etkili erişim `≥%22,5` olduğu doğrulandığı hâlde A yönlü kayma
   yoksa mevcut yeterlilik yüzeyi reddedilir.
3. H3'te başlangıç 65/35–35/65 ayrışması kurulduğu hâlde
   `I = ΔE_önde−ΔE_geride ≥ 0` bulunursa konumsal asimetri reddedilir.
4. Davranışsal DR ve güç analizi, pilot `E→DR` eğimi ve hayvan-içi varyans
   gelmeden tek bir sayıya sabitlenmez.
