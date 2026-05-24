# Firefighter Web Suite

Kullanıcı **bbox seçer → vertex çözünürlüğü verir → yangın başlangıç noktasını ve k kaynağını seçer → 8 strateji aynı anda koşar → karşılaştırma + tur-tur animasyon + sistem önerisi** döner.

İki parça:

| Katman    | Teknoloji                              | Görev                                                                                          |
| --------- | -------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Backend   | FastAPI + NetworkX + rasterio + scipy  | Bbox'tan ESA WorldCover tile indir, OSM Overpass'tan nehir/köy çek, vertex+Delaunay+engel filtresi ile graph kur, 8 algoritmayı sim et, topology fingerprint'inden öneri ver. |
| Frontend  | Vite + React + TS + Leaflet            | Leaflet ile bbox seçimi, SVG ile graph & turn-turn animasyon, strateji karşılaştırma tablosu, öneri kartı. |

## Mimari

```
final suite/
├─ ALGORITHMS.md                   stratejilerin koddan-bağımsız anlatımı
├─ map-to-graph engine/            referans Köyceğiz / Toros scriptleri (matplotlib çıktılı)
├─ backend/
│  ├─ main.py                      FastAPI app
│  ├─ map_to_graph.py              build_graph(north,south,east,west,n_vertices) -> nx.Graph
│  ├─ firefighter_engine.py        8 strateji + simulate() (mevcut engine kopyası)
│  ├─ sim_with_states.py           per-turn full state snapshot wrapper (animasyon için)
│  ├─ recommendation.py            topology fingerprint -> (primary, runner_up, reason)
│  ├─ tile_cache.py                ESA WorldCover S3 oto-indir + bbox merge
│  ├─ osm_cache.py                 Overpass nehir/yerleşim cache (User-Agent ile)
│  ├─ requirements.txt
│  └─ cache/                       (gitignored — tiles, osm json, derived graphs)
└─ frontend/
   ├─ index.html
   ├─ vite.config.ts               /api proxy -> 8765
   ├─ src/
   │  ├─ App.tsx                   üst seviye state + sekme yönetimi
   │  ├─ api.ts                    fetch wrapper + tipler
   │  ├─ MapPicker.tsx             Leaflet harita, shift-drag ile bbox
   │  ├─ ConfigPanel.tsx           sidebar form (bbox / n_vertices / fire_origin / k)
   │  ├─ GraphView.tsx             SVG render + tur-tur animasyon (play/pause/seek)
   │  ├─ ResultsTable.tsx          8 strateji × yanma % / runtime / turns
   │  ├─ Recommendation.tsx        topology fingerprint kartı + öneri
   │  └─ styles.css
   └─ package.json
```

## Çalıştırma

### 1. Backend

```bash
cd backend
python3.13 -m venv .venv             # 3.11+ olur; rasterio binary wheel'leri 3.13'te de var
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8765 --reload
```

İlk istekte ESA WorldCover tile (~50 MB / 3°×3°) indirilir; `backend/cache/tiles/` altına yazılır ve sonrakiler hızlıdır. Overpass yanıtları da `backend/cache/osm/` altında SHA1-hash isimli JSON olarak cache'lenir.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite varsayılan olarak 5173'tedir, `/api/*` istekleri `127.0.0.1:8765`'e proxylenir. Tarayıcıda `http://127.0.0.1:5173/` aç.

## Kullanım akışı

1. **Harita & bbox** sekmesi: Leaflet harita üzerinde **Shift basılı tut + sürükle** ile bbox çiz. Veya soldaki kutulara N/S/E/W elle gir. Default: Köyceğiz–Marmaris (37.10/36.87/28.66/28.40).
2. *Vertex çözünürlüğü*'nü slider'dan seç (30–60 sweet spot). **Graph oluştur**'a bas.
   * İlk istekte tile indirme + Overpass = ~5–15 sn.
   * Cache hit'ten sonra ~1 sn.
3. **Graph & yangın başlangıcı** sekmesi: SVG'de vertex'lere tıklayarak yangın başlangıç noktasını seç. Default = en yüksek dereceli vertex.
4. *k* (tur başına korunabilen vertex sayısı) ve **Tüm stratejileri çalıştır**.
5. **Sonuçlar & öneri** sekmesi:
   * Üstte sistem önerisi kartı: topology classification (`delaunay_like`, `long_thin`, `obstacles`, `hex_like`) + topology fingerprint'inden türetilen skor-tabanlı strateji önerisi + nedeni.
   * Altta tüm stratejiler tabloda — yanma %, korunan, tur, runtime — yanma %'ye göre sıralı.
   * Her satırda **İzle ▶** ile o stratejinin tur-tur yayılımı animasyonunu Graph sekmesinde göster.

## API

| Endpoint           | Method | Body                                                                  | Returns |
| ------------------ | ------ | --------------------------------------------------------------------- | ------- |
| `/api/graph`       | POST   | `{north, south, east, west, n_vertices}`                              | graph (nodes, edges, blocked_edges, settlements, raster_classes) + `graph_id` |
| `/api/simulate`    | POST   | `{graph_id, fire_origin, k, strategies?, max_turns?}`                 | her strateji için `{burned, burned_pct, turns, runtime_s, frames[], final_state}` |
| `/api/recommend`   | POST   | `{graph_id, fire_origin, k}`                                          | `{primary, runner_up, reason, confidence, scores, fingerprint}` |
| `/api/strategies`  | GET    | —                                                                     | strateji isim listesi |
| `/api/health`      | GET    | —                                                                     | `{status, cached_graphs}` |

Graph cache **in-memory**; backend restart edilince temizlenir. Tile + OSM cache disk'te kalır.

## Sınırlar / bilinen şeyler

- **k=2 default**: ALGORITHMS.md tüm benchmark'ları k=2 ile yapılmış; karşılaştırma tutarlı kalsın diye default böyle. Slider 1–6.
- **Graph cache only in memory**: `backend/cache/graphs/` rezerve edildi ama henüz kullanılmıyor; restart sonrası graph yeniden çıkarılır (tile + OSM cache'inden hızlı).
- **Random spread varyansı yok**: Engine deterministik (full neighborhood spread). Aynı (graph, fire_origin, k) her zaman aynı sonuç verir; bu yüzden Monte Carlo CI hesabı eklemedik.
- **Settlement koruma bonusu**: Şu an settlements vector overlay olarak gösteriliyor ama strateji puanlamasında ek ağırlığa sahip değil. Eklemek isterseniz `recommendation.py` ya da yeni bir `village_priority` stratejisi düşünülebilir.
- **`map-to-graph engine/` içindeki orijinal scriptler** referans olarak duruyor (matplotlib çıktısı + manuel bbox). Backend'in `map_to_graph.py`'ı bu mantığın bbox-agnostic, fonksiyonel hâli.
