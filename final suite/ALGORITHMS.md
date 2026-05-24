# Algoritmalar — koddan bağımsız anlatım

> Bu doküman **8 stratejinin** hiç koda bakmadan anlaşılabileceği biçimde
> nasıl düşündüğünü, neye baktığını ve neden o kararı verdiğini anlatır.
> Hocaya sunum hazırlarken, ekibe konuyu anlatırken, ya da sadece "bu
> algoritma neden böyle davranıyor?" sorusuna cevap ararken buraya bakın.
>
> 31 Mart toplantısında hocanın istediği "**find → check → decide**"
> anlatım kalıbı her strateji için tutarlı kullanıldı. Pseudocode YOK.

---

## 0. Ortak çerçeve — herkesin ortak başladığı yer

Her tur başında strateji **aynı 3 bilgiyi alır:**

1. **Yangın haritası** — graph üzerinde hangi düğüm RED (yanan), hangisi
   WHITE (güvenli), hangisi GREEN (korunmuş).
2. **Yangın cephesi (fire front, F)** — fire ile temas halindeki tüm
   WHITE düğümler. Yani şu an yanmamış ama bir sonraki turda yanma riski
   olan vertex'ler.
3. **Kaynak limiti (k)** — bu turda kaç vertex koruyabileceğiz. Default
   k = 2.

Her stratejinin işi **F'in içinden veya WHITE'ın içinden bir öncelik
sıralaması üretmek.** Engine bu sıralanın ilk k WHITE vertex'ini koruyup
yangın yayılımını uygular. Yani strateji aslında "**bu turda neyi
korumalıyız**" sorusunu cevaplıyor.

8 stratejiyi 3 felsefe altında topluyoruz:

- **Yerel gözlem (Greedy):** "Şu an hangi vertex en iyi görünüyor?"
- **Global yapısal (Structural):** "Graph'ın yapısı bana ne söylüyor?"
- **İleriye bakış (Lookahead):** "Bu kararı verirsem 2 tur sonra ne olur?"

---

## 1. `max_degree` — yerel, en bağlantılı vertex'i koru

**Felsefesi:** "Çok komşusu olan vertex önemlidir; korumazsam yangın oradan
çok kola yayılır."

### Find / Bul

Strateji yangın cephesindeki (F) tüm WHITE vertex'leri toplar. Her birinin
**toplam komşu sayısını** (degree) okur — komşunun WHITE/RED/GREEN olması
fark etmez.

### Check / Değerlendir

Her aday için tek skor: degree değeri. Skor ne kadar yüksekse o vertex
o kadar "topolojik olarak önemli" sayılır.

### Decide / Karar

F'i degree değerine göre büyükten küçüğe sıralar. İlk k vertex'i koruma
listesine yazar.

### Neden çalışıyor

Yüksek dereceli vertex'ler graph'ın "hub"larıdır. Yangının bunları yutması,
yangının çok daha fazla yöne aynı anda yayılmasını sağlar. Korumak bu
çoklu-yayılımı engeller.

### Neden zayıf kalıyor

"Komşu sayısı" bir vertex'in **şu an** kaç yerden ateş alacağını anlatmaz.
Bir vertex'in 8 komşusu olabilir ama hepsi RED ise, vertex zaten yanmaya
mahkum — onu korumak boşa kaynak. Daha kötüsü: vertex'in bütün komşuları
WHITE olabilir; o zaman korumak gerçekten kıymetli ama strateji bunu
ayırt etmez.

### Toy örnek üzerinden

Diyelim front'ta üç vertex var: A (5 komşu, 4'ü zaten RED), B (4 komşu,
hepsi WHITE), C (3 komşu, 2'si WHITE). max_degree A'yı seçer (degree 5).
Ama A'nın yanı sıra zaten 4 RED var, yani A korunsa bile o bölge yanıyor.
İdeal seçim B'ydi (4 WHITE komşu = 4 vertex'lik tampon kuruyor).

---

## 2. `max_white_neighbors` — yerel, en çok kurtarılabilir komşusu olanı koru

**Felsefesi:** "Bu vertex'i korursam kaç tane WHITE vertex daha hayatta
kalır?"

### Find / Bul

F'teki her vertex için **WHITE komşularını** sayar. RED komşular yok
sayılır.

### Check / Değerlendir

Tek skor: WHITE komşu sayısı. Eşitlik durumunda toplam degree tiebreaker.

### Decide / Karar

F'i WHITE-komşu sayısına göre sıralar, ilk k'yı seçer.

### Neden çalışıyor

`max_degree`'in kör noktasını kapatıyor: vertex'in **etkin** olarak ne
kadar koruma sağladığını ölçüyor. RED'lere komşu olmak skor vermiyor;
WHITE'lara komşu olmak veriyor. Yani strateji "buraya itfaiye koyarsam
gerçekten kaç ev kurtulur" diye düşünüyor.

### Bulduğumuz empirik kanıt

4 752 simülasyonda **`max_white_neighbors` her topolojide `max_degree`'i
geçti** — 14 Nisan toplantısında ekibin gözlemlediği bulgunun istatistiksel
doğrulaması. Bu, "yerel sezgi yeterli ama hangi yerel sezgiyi seçtiğin
önemli" mesajının çekirdeği.

### Neden hâlâ sınırlı

Sadece 1 adımlık bilgi alıyor: "şu anda kaç WHITE komşum var?" Yangın 2
tur sonra nereye gider, hangi koridorlardan akar — bu sorulara
duyarsız.

---

## 3. `min_cut_edge_front` — global, kenar bazlı bariyer

**Felsefesi:** "RED bölge ile WHITE bölge arasındaki en zayıf bağlantı
kenarları nerede? Onları geçen vertex'leri koruyalım."

### Find / Bul

Strateji zihinsel bir augmented graph kuruyor: tüm RED'leri ortak bir
"süper-kaynak"a, tüm WHITE'ları ortak bir "süper-hedef"e bağlar. Sanki
yangın süper-kaynaktan çıkıp WHITE bölgeye akacakmış gibi.

### Check / Değerlendir

Bu augmented graph'ta **min edge cut** hesaplar — yani süper-kaynaktan
süper-hedefe gitmeyi engellemek için silinmesi gereken minimum kenar
seti. Bu kenarlar "yangının zorunlu geçeceği koridorlar"dır.

Sonra her cut kenarın iki ucunu kontrol eder: WHITE olan uçlara puan
verir. Front'taki bir vertex ne kadar çok cut kenarın WHITE ucuysa, skoru
o kadar yüksektir.

### Decide / Karar

Front'u (cut endpoint sayısı, degree, id) sırasına göre sıralar.

### Neden çalışıyor (kısmen)

Kenar tabanlı min-cut, graph'ın yapısal "bottleneck"larını lokal
sezgiden daha iyi tespit eder. Yangının dar koridorlardan akacağı yerleri
işaret eder.

### Neden vasat çıkıyor

**Mismatch:** biz vertex koruyoruz, min-cut kenar bazlı. Cut'ın bir
tarafındaki vertex'i koruyup diğerinde aktif kenarları olduğu gibi
bırakmak, cut'ın yarısını da çözmüyor. Sayılar bunu doğruluyor: 30.9% ile
greedy'den geri kalıyor.

---

## 4. `min_damage_cut` — hocanın istediği reformülasyon

**Felsefesi:** "Min-cut'ı çöpe atmak yerine, doğru soruyu soralım: **en
çok bölgeyi en az koruyucuyla kurtaran cut hangisi?**"

### Find / Bul

Strateji RED'den her WHITE vertex'e BFS uzaklığı hesaplar. Sonra **birden
çok aday hedef bölge** dener: "RED'den en az 2 adım uzaktaki vertex'ler",
"en az 3 adım uzaktaki", "en az 4 adım uzaktaki" vs. Her aday hedef bölge
= bir **shell**.

### Check / Değerlendir

Her shell için augmented graph kurup min vertex cut hesaplar. Buraya
kadar `min_cut_vertex_front`'a benziyor. Ama kritik fark **skor**:

> **score = |kurtarılan bölge| / |cut_size|**

Yani "1 vertex koruyarak kaç vertex kurtarabilirim?" oranı.

Her shell için bu oranı hesaplar. En yüksek oran kazanır. Diğer cut'lar
elenir.

### Decide / Karar

Kazanan cut'ın WHITE vertex'lerini, front'taki olanlar önce olmak üzere
sıralar.

### Sayısal kanıt — 23% göreceli iyileştirme

Eski `min_cut_vertex_front`: 39.4% yanma. Yeni `min_damage_cut`: 30.3%
yanma. **Göreceli %23 iyileştirme** — hocanın direktifinin sayısal
karşılığı.

Bireysel senaryolarda çok daha dramatik: long-thin örneğinde "1 vertex
koruyarak 12 vertex kurtarmak" (12.00× score) görsel olarak gösterilebiliyor.

### Neden ortalama olarak yine de greedy'yi geçemedi

Ortalama 30.3%; greedy `max_white_neighbors` 29.9%. Yani **eski sürüme
göre dramatik iyileşti** ama greedy ile arada kapatamadı.

Kök neden: hesaplanan cut'ların **medyan büyüklüğü 6 vertex**, ama
elimizde **k=2 koruma**. Cut'ı tek turda tamamlayamıyoruz; ikinci turda
yangın cut'ın yarısını yutmuş oluyor. Yani algoritma doğru cut'ı buluyor
ama elimizdeki kaynak onu uygulamaya yetmiyor.

### Tek slide özet (hocaya)

> "Min-cut'ı çöpe atmadık. Sadece hangi soruyu sorduğumuzu değiştirdik.
> Yeni soru: 'hangi cut bana saved/cost oranında en iyi getiriyi verir?'
> Sonuç: eski stratejiye göre **göreceli %23 daha az yanma**, bireysel
> senaryolarda 12× kurtarma oranı."

---

## 5. `one_step_lookahead` — pair-aware ileriye bakış (en iyi)

**Felsefesi:** "Sadece 'şu an iyi' değil, '2 tur sonra ne olacak'
sorusunu cevaplayalım. Engine'in tam dinamiğini kafamızda çalıştıralım."

### Find / Bul

Önce front'tan **en umut verici 6 aday** seçer (`max_white_neighbors`
sıralamasıyla). Buradan tüm ikili kombinasyonları çıkarır: C(6,2) = 15
**aday çift**.

### Check / Değerlendir

Her çift `(v1, v2)` için **zihinsel simülasyon**:

1. State'i kopyala.
2. v1 ve v2'yi GREEN yap.
3. Yangın 1 tur yayılsın.
4. Kalan front'tan greedy `max_white_neighbors` ile 2 tane daha koru.
5. Yangın 1 tur daha yayılsın.
6. Yanan vertex sayısını say.

15 çiftin her biri için bu sayı hesaplanır. **En düşük yanmaya götüren
çift kazanır.**

### Decide / Karar

Kazanan çift en başta, kalan adaylar arkasında.

### Neden açık ara birinci (%28.1, en iyi std)

1. **Engine'in gerçek davranışını eşliyor.** Engine k=2 protect, sonra
   spread yapıyor. Lookahead bunun aynısını simüle ediyor. Greedy ya da
   cut: snapshot'a bakıp tahmin yürütüyor — lookahead direkt çalıştırıyor.
2. **Pair-awareness:** "v1 ve v2 birlikte korunsa" sorusunu görüyor.
   Saved_component bunu göremiyordu.
3. **Multi-turn dynamics:** ikinci spread step'i de simüle ettiği için
   dolaylı etkileri yakalıyor (örneğin "v1 korunmazsa onun komşu komşusu
   da yanar").

### Maliyet analizi

0.5 ms — şaşırtıcı şekilde ucuz. Sebep: top_k=6 sabit. C(6,2)=15
simülasyon, her biri 2 spread step. Toplam ~50 BFS çağrısı, çok hızlı.

### Sınırı

top_k=6 küçük graph'lar için doğru ayar. Front_size çok büyük olursa
(örneğin n=200'de) en iyi 6 aday yeterli olmayabilir; top_k'yı dinamik
ölçeklendirmek gerekir (öneri: `top_k = max(6, ceil(0.3 × front_size))`).

### Hocaya tek slide

> "Greedy + simulation hybrid: sadece 'şu an iyi' değil, '2 tur sonra
> ne olacak' sorusunu cevaplıyor. Engine'in tam mantığını kafasında
> çalıştırıyor. Sonuç: en iyi baseline'a göre **göreceli %6 iyileşme**,
> 0.5 ms maliyetinde."

---

## 6. `hybrid_density_aware` — basit if-else hibrit

**Felsefesi:** "Front darsa cut yapısı işe yarayabilir; front genişse
greedy daha doğru. Eşik üzerinden anahtarla."

### Find / Bul

Front size'ı ve toplam WHITE sayısını hesaplar.

### Check / Değerlendir

**Front yoğunluğu = front_size / white_count.**

- Yoğunluk < 0.18 ise (front küçük, dar): `min_damage_cut` çağırır.
- Yoğunluk ≥ 0.18 ise (front geniş): `max_white_neighbors` çağırır.

### Decide / Karar

Seçilen alt-stratejinin önceliklerini geçer.

### Neden mantıklı görünüyor

14 Nisan toplantısının "if-else switching" önerisinin basit
implementasyonu. Hocanın istediği "topolojiye göre uyumlu" yaklaşıma
yakın.

### Neden ortalamada parlamadı (%30.5, 5. sıra)

1. **Eşik (0.18) tuning yapılmadı.** Tahminen optimum farklı bir noktada.
2. **Switching sinyali zayıf.** Front yoğunluğu cut'ın değeri hakkında
   doğrudan bilgi vermiyor. Daha doğru sinyal: `(cut_size, score)` —
   yani hibrit, doğrudan cut'ın hesaplanmış skorunu görmeli ve karar
   vermeli.

### İyileştirme önerisi (yapılmadı)

Yeni hibrit kuralı:

- Eğer min_damage_cut hesaplandı VE cut_size ≤ k VE score ≥ 3× → cut'ı
  kullan.
- Yoksa eğer one_step_lookahead maliyeti karşılanabilir → lookahead.
- Yoksa → max_white_neighbors greedy.

Bu, 3 felsefenin orchestration'ı olur. Test edilmedi ama ranking'i
muhtemelen tepeye iter.

---

## 7. `betweenness_front` — küresel akış sezgisi

**Felsefesi:** "Bu vertex'i çıkarsam, graph'taki kaç farklı vertex çifti
arasındaki en kısa yol bozulur? Yangın da en kısa yollardan akar."

### Find / Bul

Strateji önce **WHITE alt-graf**'ı çıkarır — RED ve GREEN olan vertex'leri
yok sayar. Bu, "yangının henüz ulaşmadığı, hâlâ canlı" coğrafyaya
karşılık gelir.

### Check / Değerlendir

Bu alt-graf için **betweenness centrality** hesaplar. Bu metrik bir
vertex'in "tüm vertex çiftleri arasındaki en kısa yolların yüzde
kaçından geçtiği"ni ölçer.

Yüksek betweenness = "buradan geçmeden bir yerden bir yere gitmek zor" =
graph'ın doğal trafiği toplayan köprüsü.

### Decide / Karar

Front'u betweenness skoruna göre büyükten küçüğe sıralar.

### Neden işe yarıyor

Yangın da bir tür "trafik". RED → komşular → onların komşuları şeklinde
yayılan bilgi akışı. Yüksek betweenness'lı vertex, yangının istemeden
"köprü" olarak kullanması en muhtemel olan yer.

### Sayısal kanıt

%29.6 ile genel sıralamada 2. — sadece pair-aware lookahead'in arkasında.
`max_white_neighbors` (%29.9) ve `min_damage_cut` (%30.3) gibi tüm
diğer baseline'ları geçiyor.

**En önemli karakteristik: maliyet/performans oranı.** 2.3 ms ile
`min_damage_cut`'ın (9.5 ms) **dörtte biri** maliyetinde, üstelik daha
iyi performansla. Yani min-cut'ın çoğu sezgisini, min-cut hesaplamadan,
çok daha ucuza alıyor.

### Hocaya tek slide

> "Min-cut hesaplamak zorunda değiliz. Vertex'lerin global trafik yükünü
> ölçmek aynı bilgiyi 4× daha ucuza veriyor — üstelik biraz daha iyi
> performansla."

---

## 8. `random` — sanity baseline

Front'tan rastgele seçer. **Hiçbir bilgi kullanmıyor.** Tek amaç: diğer
stratejilerin "anlamlı bir şey yapıp yapmadığını" doğrulamak.

41.2% yanma — beklendiği gibi en kötülerden biri. Random'a yakın çıkan
herhangi bir strateji **anlamlı sinyal vermiyor demektir** ve elenebilir.

`min_cut_vertex_front` (%39.4) random'a en yakın determinist strateji —
"yapısal düşünüyorum" demek tek başına yeterli değil, **doğru yapıyı**
düşünmek gerek.

---

## 9. Üç felsefe — özet

Stratejiler 3 ana yaklaşımı temsil ediyor:

### Yerel sezgi (Greedy)

- `max_degree`, `max_white_neighbors`
- Hızlı, basit, aşırı yorumdan kaçar.
- "Şu an" sorusunu cevaplar.
- En iyi temsilci: `max_white_neighbors` (%29.9).

### Global yapısal (Structural)

- `min_cut_edge_front`, `min_damage_cut`,
  `betweenness_front`
- Graph'ın tüm yapısına bakar.
- "Doğal darboğaz nerede?" sorusunu cevaplar.
- En iyi temsilci: `betweenness_front` (%29.6) — düşük maliyetli.

### İleriye bakış (Lookahead)

- `one_step_lookahead`
- Engine'in dinamiğini kafada simüle eder.
- "2 tur sonra ne olacak?" sorusunu cevaplar.
- En iyi performans: %28.1.
