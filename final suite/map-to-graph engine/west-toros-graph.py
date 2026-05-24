# EGE GARPH.py — Vertex + Edge + Köy Koruma
import sys
try: sys.stdout.reconfigure(line_buffering=True)
except: pass

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import label as nd_label, uniform_filter
from scipy.spatial import Delaunay
from shapely.geometry import box as shapely_box, LineString, Point
from shapely.ops import unary_union
import rasterio
from rasterio.mask import mask as rio_mask
import requests

print("=== EGE GARPH ===", flush=True)

# ============================================================
# PARAMETRELER
# ============================================================
NORTH = 37.56;  SOUTH = 37.32
WEST  = 30.60;  EAST  = 30.86

DESKTOP = "/Users/efealoglu/Desktop"
TIF     = DESKTOP + "/ESA_WorldCover_10m_2021_v200_N36E030_Map.tif"
TIF_URL = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
           "v200/2021/map/ESA_WorldCover_10m_2021_v200_N36E030_Map.tif")
NPY     = DESKTOP + "/wc_toros.npy"
OUT     = DESKTOP + "/toros_graph.png"

# Yangin hassasiyet agirliklari
WMAP = {10: 5.0, 20: 3.0, 30: 1.0,
        40: 0.0, 50: 0.0, 60: 0.0, 70: 0.0, 80: 0.0, 90: 0.0}

# Engel: edge bu siniflarin uzerinden gecemez
ENGEL = {0, 40, 50, 60, 70, 80, 90}

NV        = 42    # hedef vertex sayisi (30+ serbest)
MIN_KM    = 1.5   # sadece üst üste binmeyi önle — eşit dağılım zorlanmaz
MAX_KM    = 12.0  # maksimum edge uzunlugu — çok uzak noktalar anlamsız
STEP      = 5     # piksel sub-sample
N_SAMP    = 200   # edge basi ornek

OVERPASS  = "https://overpass-api.de/api/interpreter"

# ============================================================
# 1. TIF kes, NPY kaydet
# ============================================================
print("[1] TIF kontrol / indir...", flush=True)
import os, urllib.request
if not os.path.exists(TIF):
    print(f"    Indiriliyor (~50MB): {TIF_URL}", flush=True)
    urllib.request.urlretrieve(TIF_URL, TIF)
    print("    Indirildi.", flush=True)
else:
    print(f"    Mevcut: {TIF}")

bbox_poly = shapely_box(WEST, SOUTH, EAST, NORTH)
with rasterio.open(TIF) as src:
    out_img, _ = rio_mask(src, [bbox_poly.__geo_interface__], crop=True)
wc = out_img[0]
np.save(NPY, wc)
rows, cols = wc.shape
print(f"    Boyut: {rows}x{cols}")

extent = [WEST, EAST, SOUTH, NORTH]

def pix_to_lonlat(r, c):
    return (WEST  + c*(EAST-WEST)/cols,
            NORTH + r*(SOUTH-NORTH)/rows)

def lonlat_to_pix(lon, lat):
    c = int((lon-WEST)  / (EAST-WEST)  * cols)
    r = int((lat-NORTH) / (SOUTH-NORTH) * rows)
    return r, c

# ============================================================
# 2. Agirlik + engel matrisi
# ============================================================
print("[2] Matrisler", flush=True)
weight   = np.zeros_like(wc, dtype=float)
obstacle = np.zeros_like(wc, dtype=bool)
for code, val in WMAP.items():
    weight[wc == code] = val
for code in ENGEL:
    obstacle[wc == code] = True

u, cnt = np.unique(wc, return_counts=True)
SINIF = {10:"Orman", 20:"Maki", 30:"Otlak", 40:"Tarim",
         50:"Yapi", 60:"Ciplak", 80:"Su", 90:"Sulak"}
for uu, cc in zip(u, cnt):
    print(f"    {uu:3d} {SINIF.get(int(uu),'?'):10s} {cc:8,} px")

# ============================================================
# 3. Su siniflandirma (deniz / gol)
# ============================================================
print("[3] Su siniflandirma", flush=True)
water = (wc == 80)
labeled, _ = nd_label(water)
border_lbl = set()
border_lbl.update(labeled[-1,:]); border_lbl.update(labeled[:,0])
border_lbl.update(labeled[:,-1]); border_lbl.discard(0)
sea_mask  = np.isin(labeled, list(border_lbl)) & water
lake_mask = water & ~sea_mask
print(f"    Deniz: {sea_mask.sum():,}  Gol: {lake_mask.sum():,} px")

# ============================================================
# 4. Overpass: nehirler
# ============================================================
print("[4] Nehir verisi", flush=True)
river_lines = []
q_river = f"""
[out:json][timeout:90];
(way["waterway"]({SOUTH},{WEST},{NORTH},{EAST}););
out geom;
"""
try:
    r = requests.post(OVERPASS, data={"data": q_river}, timeout=120)
    WW = {"river":2.5,"canal":2.0,"stream":1.2,"drain":0.7,"ditch":0.5}
    for el in r.json().get("elements",[]):
        if el["type"]=="way" and "geometry" in el:
            coords = [(p["lon"],p["lat"]) for p in el["geometry"]]
            if len(coords)>=2:
                tags = el.get("tags",{})
                wt   = tags.get("waterway","stream")
                river_lines.append({
                    "geom": LineString(coords),
                    "type": wt,
                    "lw":   WW.get(wt,0.6),
                    "name": tags.get("name",""),
                })
    print(f"    {len(river_lines)} waterway")
except Exception as e:
    print(f"    HATA: {e}")

# ============================================================
# 5. Overpass: köyler / yerlesim yerleri
# ============================================================
print("[5] Yerlesim yerleri", flush=True)
villages = []
q_village = f"""
[out:json][timeout:60];
(
  node["place"~"^(village|hamlet|town|suburb)$"]({SOUTH},{WEST},{NORTH},{EAST});
);
out body;
"""
try:
    r = requests.post(OVERPASS, data={"data": q_village}, timeout=90)
    for el in r.json().get("elements",[]):
        if el["type"]=="node":
            tags = el.get("tags",{})
            name = tags.get("name", tags.get("name:tr","?"))
            place = tags.get("place","village")
            villages.append({
                "lon":  el["lon"],
                "lat":  el["lat"],
                "name": name,
                "type": place,
            })
    print(f"    {len(villages)} yerlesim bulundu:")
    for v in villages:
        print(f"      {v['type']:8s} {v['name']}  ({v['lon']:.4f}, {v['lat']:.4f})")
except Exception as e:
    print(f"    HATA: {e}")

# ---- Vektör engel geometrileri (edge filtresi için) ----
# Sadece büyük nehirler (river/canal) vektör engeli — derecikler raster'a bırakılır
RIVER_BUF_DEG = 80 / 111_000   # 80m buffer
major_rivers = [rl for rl in river_lines if rl["type"] in ("river", "canal")]
river_union = (unary_union([rl["geom"].buffer(RIVER_BUF_DEG) for rl in major_rivers])
               if major_rivers else None)
print(f"    Büyük nehir vektör engeli: {len(major_rivers)} hat, 80m buffer")

# Köy buffer: her köy merkezi etrafında 600m yasak bölge
VILLAGE_BUF_DEG = 600 / 111_000
village_geoms = [
    Point(v["lon"], v["lat"]).buffer(VILLAGE_BUF_DEG)
    for v in villages
]
village_union = unary_union(village_geoms) if village_geoms else None
if village_union:
    print(f"    Köy engel buffer: {len(village_geoms)} köy, 600m radius")

# ============================================================
# 6. Vertex yerlestirme — orman yogunluguna göre agirlikli
# ============================================================
print("[6] Vertex yerlestiriliyor", flush=True)
min_dist_deg = MIN_KM / 111.0

ri = np.arange(0, rows, STEP)
ci = np.arange(0, cols, STEP)
rr, cc_a = np.meshgrid(ri, ci, indexing="ij")
rr, cc_a = rr.flatten(), cc_a.flatten()

# --- Yerel orman yoğunluk haritası ---
# 500m yarıçaplı komşuluk ortalaması (kernel ~50px at 10m/px)
forest_binary = (wc == 10).astype(np.float32)
KS = 101  # ~500m yarıçap (daha geniş komşuluk = daha güvenilir yoğunluk)
local_density = uniform_filter(forest_binary, size=KS)
local_density[obstacle] = 0.0

# Bbox kenarından 1.5km buffer — sınıra yapışan vertex olmasın
border_km   = 1.5
border_r    = int(border_km / 111.0 / (NORTH - SOUTH) * rows)
border_c    = int(border_km / 111.0 / (EAST  - WEST)  * cols)
border_mask = np.zeros_like(local_density, dtype=bool)
border_mask[:border_r, :]  = True  # kuzey kenar
border_mask[-border_r:, :] = True  # güney kenar
border_mask[:, :border_c]  = True  # batı kenar
border_mask[:, -border_c:] = True  # doğu kenar
local_density[border_mask] = 0.0

MIN_DENSITY = 0.75  # vertex için min yerel orman yoğunluğu
n_eligible = (local_density >= MIN_DENSITY).sum()
print(f"    Eşik >= %75: {n_eligible:,} px uygun ({100*n_eligible/(rows*cols):.1f}% alan)")

# Bölgeye özgü EDGE_DENSITY_MIN — orman piksellerinin %25'lik dilimi
_dens_forest = local_density[(wc == 10) & ~obstacle]
EDGE_DENSITY_MIN = float(np.percentile(_dens_forest, 25)) if len(_dens_forest) > 0 else 0.30
print(f"    EDGE_DENSITY_MIN (bölgeye özgü): {EDGE_DENSITY_MIN:.2f}")

# --- 2 fazlı vertex yerleştirme ---
# Faz 1: Izgara bazlı alan kapsaması — büyük alanlara garanti vertex
# Faz 2: Yoğunluk sıralamalı ek vertex — yoğun alanlara ekstra
eligible_mask = (local_density >= MIN_DENSITY)

vertices  = []
seen_rc   = set()

# -- Faz 1: 6×6 = 36 ızgara hücre, her uygun hücreye 1 vertex --
G = 6
cell_r_g  = rows // G
cell_c_g  = cols // G
grid_cands = []
for gr in range(G):
    for gc in range(G):
        r0, r1 = gr*cell_r_g, min((gr+1)*cell_r_g, rows)
        c0, c1 = gc*cell_c_g, min((gc+1)*cell_c_g, cols)
        cell_ld = local_density[r0:r1, c0:c1].copy()
        cell_ld[~eligible_mask[r0:r1, c0:c1]] = 0.0
        if cell_ld.max() == 0:
            continue
        best = np.unravel_index(cell_ld.argmax(), cell_ld.shape)
        grid_cands.append((cell_ld[best], r0+best[0], c0+best[1]))

grid_cands.sort(reverse=True)
for dens, r, c in grid_cands:
    lon, lat = pix_to_lonlat(r, c)
    if any(((lon-vx)**2+(lat-vy)**2)**0.5 < min_dist_deg for vx, vy in vertices):
        continue
    vertices.append((lon, lat))
    seen_rc.add((r, c))

print(f"    Izgara fazı: {len(vertices)} vertex")

# -- Faz 2: Yoğunluk sıralamalı ek vertex (NV'e tamamla) --
ri_sub = np.arange(0, rows, STEP)
ci_sub = np.arange(0, cols, STEP)
rr_g, cc_g = np.meshgrid(ri_sub, ci_sub, indexing="ij")
rr_g, cc_g  = rr_g.flatten(), cc_g.flatten()
ld_filtered  = np.where(eligible_mask[rr_g, cc_g], local_density[rr_g, cc_g], 0.0)
sorted_idx   = np.argsort(-ld_filtered)

for idx in sorted_idx:
    if len(vertices) >= NV:
        break
    if ld_filtered[idx] == 0:
        break
    r, c = rr_g[idx], cc_g[idx]
    if (r, c) in seen_rc:
        continue
    lon, lat = pix_to_lonlat(r, c)
    if any(((lon-vx)**2+(lat-vy)**2)**0.5 < min_dist_deg for vx, vy in vertices):
        continue
    vertices.append((lon, lat))
    seen_rc.add((r, c))

# Vertex 1 ile Vertex 2 arasına yoğunluk bazlı ek vertex
v1_lon, v1_lat = vertices[1]
v2_lon, v2_lat = vertices[2]
mx, my = (v1_lon + v2_lon) / 2, (v1_lat + v2_lat) / 2
search_r = ((v1_lon-v2_lon)**2 + (v1_lat-v2_lat)**2)**0.5 * 0.7

best_dens, best_r, best_c = 0.0, -1, -1
for ri_s in range(0, rows, STEP):
    for ci_s in range(0, cols, STEP):
        if not eligible_mask[ri_s, ci_s]:
            continue
        lon_s, lat_s = pix_to_lonlat(ri_s, ci_s)
        if ((lon_s-mx)**2 + (lat_s-my)**2)**0.5 > search_r:
            continue
        if any(((lon_s-vx)**2+(lat_s-vy)**2)**0.5 < min_dist_deg
               for vx, vy in vertices):
            continue
        if local_density[ri_s, ci_s] > best_dens:
            best_dens, best_r, best_c = local_density[ri_s, ci_s], ri_s, ci_s

if best_r >= 0:
    new_lon, new_lat = pix_to_lonlat(best_r, best_c)
    vertices.append((new_lon, new_lat))
    print(f"    Ek vertex (V1-V2 arası): ({new_lon:.4f}, {new_lat:.4f})  yoğunluk=%{best_dens*100:.0f}")
else:
    print("    UYARI: V1-V2 arası ek vertex için uygun piksel bulunamadı")

vertices = np.array(vertices)
print(f"    {len(vertices)} vertex yerlestirildi")

# Her vertex'in yerel orman yoğunluğunu yazdır (sunum kontrolü)
print("    Vertex orman yogunluklari:")
for i, (lon, lat) in enumerate(vertices):
    r, c = lonlat_to_pix(lon, lat)
    r = max(0, min(r, rows-1))
    c = max(0, min(c, cols-1))
    dens = local_density[r, c]
    cls  = wc[r, c]
    print(f"      V{i:02d}: class={cls:2d}  yerel_yogunluk=%{dens*100:.0f}")

# ============================================================
# 7. Delaunay triangulation
# ============================================================
print("[7] Delaunay + uzunluk filtresi", flush=True)
tri = Delaunay(vertices)
all_edges = set()
for s in tri.simplices:
    for i in range(3):
        a, b = s[i], s[(i+1)%3]
        all_edges.add((min(a,b), max(a,b)))

# Çok uzun edge'leri çıkar — yangın yayılımı için anlamsız
max_deg = MAX_KM / 111.0
all_edges = [
    (a, b) for a, b in all_edges
    if ((vertices[a][0]-vertices[b][0])**2 +
        (vertices[a][1]-vertices[b][1])**2)**0.5 <= max_deg
]
print(f"    {len(all_edges)} edge (max {MAX_KM} km filtresi sonrası)")

# ============================================================
# 8. Engel filtresi — raster piksel örnekleme
# ============================================================
print("[8] Engel filtresi", flush=True)

# Ateşin yayılabileceği sınıflar: sadece orman (10) ve maki (20)
FIRE_CLASSES = {10, 20}

# Bariyer sayılmak için gereken minimum boşluk genişliği (metre)
# Bundan dar ormansız alanlar → aktif edge (yangın atlayabilir)
# Bundan geniş nehir/boşluk  → pasif edge (geçilemez)
MIN_GAP_M = 150

def hits_obstacle(v1, v2):
    line = LineString([v1, v2])

    # 1) Vektör: büyük nehir / kanal
    if river_union and line.intersects(river_union):
        return True

    # 2) Vektör: köy buffer
    if village_union and line.intersects(village_union):
        return True

    # 3) Raster: art arda ormansız piksel uzunluğunu ölç
    lons = np.linspace(v1[0], v2[0], N_SAMP)
    lats = np.linspace(v1[1], v2[1], N_SAMP)
    edge_km = ((v1[0]-v2[0])**2 + (v1[1]-v2[1])**2)**0.5 * 111.0
    m_per_sample = edge_km * 1000 / N_SAMP
    n_tol = max(1, int(MIN_GAP_M / m_per_sample))  # kaç örnek = 150m

    run = 0  # art arda ormansız örnek sayacı
    for lon, lat in zip(lons, lats):
        r, c = lonlat_to_pix(lon, lat)
        if not (0 <= r < rows and 0 <= c < cols):
            continue
        cls = int(wc[r, c])
        if cls == 80:          # Su — tolerans yok, anında pasif
            return True
        is_barrier = obstacle[r, c] or (cls not in FIRE_CLASSES) or (local_density[r, c] < EDGE_DENSITY_MIN)
        if is_barrier:
            run += 1
            if run >= n_tol:   # 150m'den geniş → pasif
                return True
        else:
            run = 0            # orman geri geldi, sayacı sıfırla

    return False

valid_edges, blocked_edges = [], []
for a, b in all_edges:
    (blocked_edges if hits_obstacle(vertices[a], vertices[b])
     else valid_edges).append((a, b))

print(f"    Gecerli : {len(valid_edges)}")
print(f"    Pasif   : {len(blocked_edges)}")
print(f"    Oran    : %{100*len(blocked_edges)//len(all_edges)}")

# Manuel pasif edge'ler — algoritmadan bağımsız olarak zorla pasif
MANUAL_BLOCKED = {(min(a,b), max(a,b)) for a,b in
                  [(0,1),(0,3),(0,4),(3,5),(5,11),(11,12),(20,22),(22,29)]}
new_valid, new_blocked = [], list(blocked_edges)
for a, b in valid_edges:
    key = (min(a,b), max(a,b))
    if key in MANUAL_BLOCKED:
        new_blocked.append((a, b))
    else:
        new_valid.append((a, b))
valid_edges, blocked_edges = new_valid, new_blocked
print(f"    Manuel pasif: {sorted(MANUAL_BLOCKED)}")

# ============================================================
# 9. GORSEL
# ============================================================
print("[9] Gorsel", flush=True)

cmap_fire = LinearSegmentedColormap.from_list(
    "fire", ["#ffffd4","#fed976","#fd8d3c","#e31a1c","#800026"])

fig, ax = plt.subplots(figsize=(13, 10))
fig.patch.set_facecolor("white")

# Yangin hassasiyeti arka plan
im = ax.imshow(weight, extent=extent, origin="upper",
               cmap=cmap_fire, vmin=0, vmax=5, aspect="auto", alpha=0.88)

def solid_cmap(hex_color):
    return LinearSegmentedColormap.from_list("", [hex_color, hex_color])

# Tarim
ax.imshow(np.where(wc==40, 1., np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#f5deb3"), vmin=0, vmax=1, aspect="auto", alpha=0.82, zorder=2)

# Yapi + Ciplak
ax.imshow(np.where((wc==50)|(wc==60), 1., np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#b0b0b0"), vmin=0, vmax=1, aspect="auto", alpha=0.82, zorder=2)

# Sulak alan
ax.imshow(np.where(wc==90, 1., np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#7ecbc8"), vmin=0, vmax=1, aspect="auto", alpha=0.80, zorder=3)

# Deniz
ax.imshow(np.where(sea_mask, 1., np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#9ecae1"), vmin=0, vmax=1, aspect="auto", alpha=0.92, zorder=4)

# Gol
ax.imshow(np.where(lake_mask, 1., np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#2171b5"), vmin=0, vmax=1, aspect="auto", alpha=0.95, zorder=5)

# Nehirler — beyaz glow + renkli ic hat
for rl in river_lines:
    xy = list(rl["geom"].coords)
    xs = [p[0] for p in xy]
    ys = [p[1] for p in xy]
    lw = rl["lw"]
    color    = "#0066cc" if rl["type"] in ("river","canal") else "#2196f3"
    lw_inner = lw * 2.8   if rl["type"] in ("river","canal") else lw * 1.8
    ax.plot(xs, ys, color="white", lw=lw_inner+2.0,
            alpha=0.85, zorder=6, solid_capstyle="round")
    ax.plot(xs, ys, color=color,  lw=lw_inner,
            alpha=0.95, zorder=7, solid_capstyle="round")

# Pasif edge'ler — kesik kirmizi
for a, b in blocked_edges:
    ax.plot([vertices[a][0], vertices[b][0]],
            [vertices[a][1], vertices[b][1]],
            color="#cc0000", linestyle="--", lw=0.9, alpha=0.50, zorder=8)

# Aktif edge'ler — koyu yesil
for a, b in valid_edges:
    ax.plot([vertices[a][0], vertices[b][0]],
            [vertices[a][1], vertices[b][1]],
            color="#1a6b1a", lw=1.8, alpha=0.85, zorder=9)

# Vertex'ler — tek tip, siyah nokta
for i, (lon, lat) in enumerate(vertices):
    ax.scatter(lon, lat, s=120, c="#111111", zorder=10,
               edgecolors="white", linewidths=0.9)
    ax.annotate(str(i+1), (lon, lat), fontsize=6,
                ha="center", va="center",
                color="white", fontweight="bold", zorder=11)

# Köyler — turuncu halka + isim
PLACE_SIZE = {"town":220, "suburb":180, "village":140, "hamlet":100}
for v in villages:
    sz = PLACE_SIZE.get(v["type"], 140)
    ax.scatter(v["lon"], v["lat"], s=sz*3, c="none",
               edgecolors="#ff6600", linewidths=2.2, zorder=11, marker="o")
    ax.scatter(v["lon"], v["lat"], s=sz*0.6, c="#ff6600",
               zorder=12, marker="*")
    ax.annotate(v["name"], (v["lon"], v["lat"]),
                xytext=(5, 6), textcoords="offset points",
                fontsize=8, fontweight="bold", color="#cc4400",
                bbox=dict(boxstyle="round,pad=0.2", fc="white",
                          ec="#ff6600", lw=0.8, alpha=0.85),
                zorder=13)

# Colorbar
cb = plt.colorbar(im, ax=ax, shrink=0.40, pad=0.01, aspect=16)
cb.set_label("Yangın Hassasiyeti", fontsize=9, rotation=270, labelpad=14)
cb.set_ticks([0,1,2,3,4,5])
cb.set_ticklabels(["0\nSu/Yapı","1\nOtlak","2","3\nMaki","4","5\nOrman"])

# Legend — haritanın dışında sağda
handles = [
    mpatches.Patch(facecolor="#9ecae1", ec="#555", lw=0.5, label="Deniz"),
    mpatches.Patch(facecolor="#2171b5", ec="#555", lw=0.5, label="Göl"),
    mpatches.Patch(facecolor="#7ecbc8", ec="#555", lw=0.5, label="Sulak alan"),
    plt.Line2D([0],[0], color="#0066cc", lw=2,   label="Nehir / Kanal"),
    plt.Line2D([0],[0], color="#2196f3", lw=1.2, label="Dere"),
    mpatches.Patch(facecolor="#b0b0b0", ec="#555", lw=0.5, label="Yapı / Çıplak"),
    mpatches.Patch(facecolor="#f5deb3", ec="#555", lw=0.5, label="Tarım"),
    plt.Line2D([0],[0], color="#1a6b1a", lw=2,   label="Aktif edge"),
    plt.Line2D([0],[0], color="#cc0000", lw=1, ls="--", label="Pasif edge (bariyer)"),
    plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="#111111",
               markersize=8, label="Vertex"),
    plt.Line2D([0],[0], marker="*", color="w", markerfacecolor="#ff6600",
               markersize=10, label="Köy (öncelikli koruma)"),
]
ax.legend(handles=handles, loc="upper left", fontsize=8.5,
          framealpha=0.95, edgecolor="#aaa",
          title="Açıklama", title_fontsize=9,
          bbox_to_anchor=(1.01, 1), borderaxespad=0)

nv, nb = len(valid_edges), len(blocked_edges)
ax.set_title(
    f"Batı Toros Dağları (Antalya) ~612 km²  |  {len(vertices)} vertex  |  "
    f"{nv} aktif, {nb} pasif edge\n"
    f"Engeller: Su · Tarım · Yapı · Çıplak · Nehir · Köy",
    fontsize=11, fontweight="bold", pad=10
)
ax.set_xlabel("Boylam", fontsize=10)
ax.set_ylabel("Enlem",  fontsize=10)
ax.set_xlim(WEST, EAST)
ax.set_ylim(SOUTH, NORTH)
ax.tick_params(labelsize=9)
ax.grid(color="white", alpha=0.15, lw=0.4)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
print(f"    Kaydedildi: {OUT}", flush=True)
plt.show()
print("=== BITTI ===", flush=True)
