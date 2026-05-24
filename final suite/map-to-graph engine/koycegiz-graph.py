# EGE GARPH.py — Köyceğiz–Marmaris Yangın Yayılım Grafı
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
NORTH = 37.10;  SOUTH = 36.87
WEST  = 28.40;  EAST  = 28.66

DESKTOP = "/Users/efealoglu/Desktop"
TIF     = DESKTOP + "/ESA_WorldCover_10m_2021_v200_N36E027_Map.tif"
OUT     = DESKTOP + "/final_graph.png"

WMAP  = {10:5.0, 20:3.0, 30:1.0, 40:0.0, 50:0.0, 60:0.0, 70:0.0, 80:0.0, 90:0.0}
ENGEL = {0, 40, 50, 60, 70, 80, 90}

NV      = 40     # hedef vertex sayısı
MIN_KM  = 1.5    # Poisson-disk min mesafe
MAX_KM  = 14.0   # Delaunay çok uzak edge filtresi
STEP    = 5
N_SAMP  = 200

# Yangın yayılabilen sınıflar — sadece doğal engel, density kısıtı yok
FIRE_CLASSES = {10, 20}
MIN_GAP_M    = 100   # bu kadar dar ormansız bant tolere edilir

OVERPASS = "https://overpass-api.de/api/interpreter"

# ============================================================
# 1. TIF kes
# ============================================================
print("[1] TIF kesiliyor...", flush=True)
bbox_poly = shapely_box(WEST, SOUTH, EAST, NORTH)
with rasterio.open(TIF) as src:
    out_img, _ = rio_mask(src, [bbox_poly.__geo_interface__], crop=True)
wc = out_img[0]
rows, cols = wc.shape
print(f"    Boyut: {rows}x{cols}")
extent = [WEST, EAST, SOUTH, NORTH]

def pix_to_lonlat(r, c):
    return (WEST + c*(EAST-WEST)/cols, NORTH + r*(SOUTH-NORTH)/rows)

def lonlat_to_pix(lon, lat):
    return (int((lat-NORTH)/(SOUTH-NORTH)*rows),
            int((lon-WEST) /(EAST-WEST) *cols))

# ============================================================
# 2. Ağırlık + engel
# ============================================================
print("[2] Matrisler", flush=True)
weight   = np.zeros_like(wc, dtype=float)
obstacle = np.zeros_like(wc, dtype=bool)
for code, val in WMAP.items():  weight[wc==code] = val
for code in ENGEL:              obstacle[wc==code] = True

SINIF = {10:"Orman",20:"Maki",30:"Otlak",40:"Tarim",
         50:"Yapi",60:"Ciplak",80:"Su",90:"Sulak"}
for uu, cc in zip(*np.unique(wc, return_counts=True)):
    print(f"    {uu:3d} {SINIF.get(int(uu),'?'):10s} {cc:8,} px")

# ============================================================
# 3. Su sınıflandırma
# ============================================================
print("[3] Su siniflandirma", flush=True)
water = (wc == 80)
labeled, _ = nd_label(water)
border_lbl = set()
border_lbl.update(labeled[0,:]); border_lbl.update(labeled[-1,:])
border_lbl.update(labeled[:,0]); border_lbl.update(labeled[:,-1])
border_lbl.discard(0)
sea_mask  = np.isin(labeled, list(border_lbl)) & water
lake_mask = water & ~sea_mask
print(f"    Deniz: {sea_mask.sum():,}  Göl: {lake_mask.sum():,} px")

# ============================================================
# 4. OSM Nehirler
# ============================================================
print("[4] Nehir verisi", flush=True)
river_lines = []
try:
    q = f"""[out:json][timeout:90];
(way["waterway"]({SOUTH},{WEST},{NORTH},{EAST}););
out geom;"""
    resp = requests.post(OVERPASS, data={"data":q}, timeout=120)
    WW = {"river":2.5,"canal":2.0,"stream":1.2,"drain":0.7,"ditch":0.5}
    for el in resp.json().get("elements",[]):
        if el["type"]=="way" and "geometry" in el:
            coords = [(p["lon"],p["lat"]) for p in el["geometry"]]
            if len(coords)>=2:
                tags = el.get("tags",{})
                wt   = tags.get("waterway","stream")
                river_lines.append({"geom":LineString(coords),
                                    "type":wt, "lw":WW.get(wt,0.6),
                                    "name":tags.get("name","")})
    print(f"    {len(river_lines)} waterway")
except Exception as e:
    print(f"    HATA: {e}")

# ============================================================
# 5. OSM Köyler
# ============================================================
print("[5] Yerlesim yerleri", flush=True)
villages = []
try:
    q = f"""[out:json][timeout:60];
(node["place"~"^(village|hamlet|town|suburb)$"]({SOUTH},{WEST},{NORTH},{EAST}););
out body;"""
    resp = requests.post(OVERPASS, data={"data":q}, timeout=90)
    for el in resp.json().get("elements",[]):
        if el["type"]=="node":
            tags = el.get("tags",{})
            villages.append({"lon":el["lon"],"lat":el["lat"],
                             "name":tags.get("name",tags.get("name:tr","?")),
                             "type":tags.get("place","village")})
    print(f"    {len(villages)} yerlesim:")
    for v in villages:
        print(f"      {v['type']:8s} {v['name']}  ({v['lon']:.4f},{v['lat']:.4f})")
except Exception as e:
    print(f"    HATA: {e}")

# Vektör engel geometrileri
major_rivers = [rl for rl in river_lines if rl["type"] in ("river","canal")]
river_union  = (unary_union([rl["geom"].buffer(80/111_000) for rl in major_rivers])
                if major_rivers else None)
print(f"    Büyük nehir buffer: {len(major_rivers)} hat")

village_union = (unary_union([Point(v["lon"],v["lat"]).buffer(600/111_000) for v in villages])
                 if villages else None)
print(f"    Köy buffer: {len(villages)} yerlesim")

# ============================================================
# 6. Vertex yerleştirme — 2 fazlı (ızgara + yoğunluk)
# ============================================================
print("[6] Vertex yerlestiriliyor", flush=True)
min_dist_deg = MIN_KM / 111.0

# Yerel orman yoğunluğu (class 10, 1km kernel)
forest_binary = (wc == 10).astype(np.float32)
KS = 101
local_density = uniform_filter(forest_binary, size=KS)
local_density[obstacle] = 0.0

# Sınır tamponu 1.5km
br = int(1.5/111.0/(NORTH-SOUTH)*rows)
bc = int(1.5/111.0/(EAST-WEST)*cols)
bm = np.zeros_like(local_density, dtype=bool)
bm[:br,:]=True; bm[-br:,:]=True; bm[:,:bc]=True; bm[:,-bc:]=True
local_density[bm] = 0.0

# Köyceğiz bölgesi için MIN_DENSITY — bölgedeki orman dağılımına göre
# %40 eşiği: hem yoğun hem orta yoğunluklu orman alanları dahil olur
MIN_DENSITY = 0.40
n_elig = (local_density >= MIN_DENSITY).sum()
print(f"    Uygun piksel (>=%{int(MIN_DENSITY*100)}): {n_elig:,}  ({100*n_elig/(rows*cols):.1f}% alan)")

eligible_mask = (local_density >= MIN_DENSITY)
vertices = []
seen_rc  = set()

# Faz 1 — 6×6 ızgara, her hücreye garanti 1 vertex
G = 6
cr, cc_ = rows//G, cols//G
grid_cands = []
for gr in range(G):
    for gc in range(G):
        r0,r1 = gr*cr, min((gr+1)*cr, rows)
        c0,c1 = gc*cc_, min((gc+1)*cc_, cols)
        cell = local_density[r0:r1, c0:c1].copy()
        cell[~eligible_mask[r0:r1, c0:c1]] = 0.0
        if cell.max() == 0: continue
        br2, bc2 = np.unravel_index(cell.argmax(), cell.shape)
        grid_cands.append((cell[br2,bc2], r0+br2, c0+bc2))

grid_cands.sort(reverse=True)
for dens, r, c in grid_cands:
    lon, lat = pix_to_lonlat(r, c)
    if any(((lon-vx)**2+(lat-vy)**2)**0.5 < min_dist_deg for vx,vy in vertices):
        continue
    vertices.append((lon, lat))
    seen_rc.add((r, c))
print(f"    Izgara fazı: {len(vertices)} vertex")

# Faz 2 — yoğunluk sıralı ek vertex (NV'e tamamla)
ri_s = np.arange(0, rows, STEP)
ci_s = np.arange(0, cols, STEP)
rr_g, cc_g = np.meshgrid(ri_s, ci_s, indexing="ij")
rr_g, cc_g = rr_g.flatten(), cc_g.flatten()
ld_f = np.where(eligible_mask[rr_g, cc_g], local_density[rr_g, cc_g], 0.0)
for idx in np.argsort(-ld_f):
    if len(vertices) >= NV: break
    if ld_f[idx] == 0: break
    r, c = rr_g[idx], cc_g[idx]
    if (r,c) in seen_rc: continue
    lon, lat = pix_to_lonlat(r, c)
    if any(((lon-vx)**2+(lat-vy)**2)**0.5 < min_dist_deg for vx,vy in vertices):
        continue
    vertices.append((lon, lat))
    seen_rc.add((r, c))

# Cluster seyreltme — 2.0km min mesafe ile fazla yoğun alanı seyrelt
THIN_DEG = 2.0 / 111.0
thinned = []
for vx, vy in vertices:
    if any(((vx-tx)**2+(vy-ty)**2)**0.5 < THIN_DEG for tx,ty in thinned):
        continue
    thinned.append((vx, vy))
print(f"    Seyreltme: {len(vertices)} → {len(thinned)} vertex")

# Zorla eklenen koordinat (kullanıcı belirtti)
FORCED = (28.4155, 36.9158)
if all(((FORCED[0]-vx)**2+(FORCED[1]-vy)**2)**0.5 > (1.5/111.0) for vx,vy in thinned):
    thinned.append(FORCED)
    print(f"    Forced vertex eklendi: {FORCED}")

vertices = np.array(thinned)
print(f"    Toplam: {len(vertices)} vertex")
for i,(lon,lat) in enumerate(vertices):
    r,c = lonlat_to_pix(lon,lat)
    r=np.clip(r,0,rows-1); c=np.clip(c,0,cols-1)
    print(f"      V{i+1:02d}: class={wc[r,c]:2d}  yogunluk=%{local_density[r,c]*100:.0f}")

# ============================================================
# 7. Delaunay
# ============================================================
print("[7] Delaunay", flush=True)
tri = Delaunay(vertices)
all_edges = set()
for s in tri.simplices:
    for i in range(3):
        a,b = s[i], s[(i+1)%3]
        all_edges.add((min(a,b), max(a,b)))
max_deg = MAX_KM/111.0
all_edges = [(a,b) for a,b in all_edges
             if ((vertices[a][0]-vertices[b][0])**2+
                 (vertices[a][1]-vertices[b][1])**2)**0.5 <= max_deg]
print(f"    {len(all_edges)} edge (max {MAX_KM}km sonrası)")

# ============================================================
# 8. Engel filtresi — sadece doğal koşullar
# ============================================================
print("[8] Engel filtresi", flush=True)

def hits_obstacle(v1, v2):
    line = LineString([v1, v2])
    if river_union and line.intersects(river_union):  return True
    if village_union and line.intersects(village_union): return True

    lons = np.linspace(v1[0], v2[0], N_SAMP)
    lats = np.linspace(v1[1], v2[1], N_SAMP)
    edge_km  = ((v1[0]-v2[0])**2+(v1[1]-v2[1])**2)**0.5 * 111.0
    m_per_s  = edge_km * 1000 / N_SAMP
    n_tol    = max(1, int(MIN_GAP_M / m_per_s))
    run = 0
    for lon, lat in zip(lons, lats):
        r, c = lonlat_to_pix(lon, lat)
        if not (0<=r<rows and 0<=c<cols): continue
        cls = int(wc[r, c])
        if cls == 80: return True          # Su — toleranssız
        if cls not in FIRE_CLASSES:
            run += 1
            if run >= n_tol: return True   # geniş ormansız bant
        else:
            run = 0
    return False

valid_edges, blocked_edges = [], []
for a, b in all_edges:
    (blocked_edges if hits_obstacle(vertices[a], vertices[b])
     else valid_edges).append((a, b))
print(f"    Gecerli: {len(valid_edges)}  Pasif: {len(blocked_edges)}")

# Manuel pasif — görüntüdeki 1-indexed numaralara göre (18-39, 8-36)
MANUAL_BLOCKED = {(min(17,38), max(17,38)), (min(7,35), max(7,35)), (min(16,30), max(16,30))}
new_valid, new_blocked = [], list(blocked_edges)
for a, b in valid_edges:
    key = (min(a,b), max(a,b))
    if key in MANUAL_BLOCKED:
        new_blocked.append((a, b))
        print(f"    Manuel pasif: V{a+1}–V{b+1}")
    else:
        new_valid.append((a, b))
valid_edges, blocked_edges = new_valid, new_blocked

# ============================================================
# 9. GÖRSEL
# ============================================================
print("[9] Gorsel", flush=True)
cmap_fire = LinearSegmentedColormap.from_list(
    "fire", ["#ffffd4","#fed976","#fd8d3c","#e31a1c","#800026"])

fig, ax = plt.subplots(figsize=(13, 11))
fig.patch.set_facecolor("white")

def solid_cmap(c): return LinearSegmentedColormap.from_list("",[c,c])

im = ax.imshow(weight, extent=extent, origin="upper",
               cmap=cmap_fire, vmin=0, vmax=5, aspect="auto", alpha=0.88)
ax.imshow(np.where(wc==40,1.,np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#f5deb3"), vmin=0,vmax=1, aspect="auto", alpha=0.82, zorder=2)
ax.imshow(np.where((wc==50)|(wc==60),1.,np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#b0b0b0"), vmin=0,vmax=1, aspect="auto", alpha=0.82, zorder=2)
ax.imshow(np.where(wc==90,1.,np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#7ecbc8"), vmin=0,vmax=1, aspect="auto", alpha=0.80, zorder=3)
ax.imshow(np.where(sea_mask,1.,np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#9ecae1"), vmin=0,vmax=1, aspect="auto", alpha=0.92, zorder=4)
ax.imshow(np.where(lake_mask,1.,np.nan), extent=extent, origin="upper",
          cmap=solid_cmap("#2171b5"), vmin=0,vmax=1, aspect="auto", alpha=0.95, zorder=5)

for rl in river_lines:
    xy = list(rl["geom"].coords)
    xs=[p[0] for p in xy]; ys=[p[1] for p in xy]
    clr = "#0066cc" if rl["type"] in ("river","canal") else "#2196f3"
    lw  = rl["lw"]*(2.8 if rl["type"] in ("river","canal") else 1.8)
    ax.plot(xs,ys,color="white",lw=lw+2.0,alpha=0.85,zorder=6,solid_capstyle="round")
    ax.plot(xs,ys,color=clr,   lw=lw,    alpha=0.95,zorder=7,solid_capstyle="round")

for a,b in blocked_edges:
    ax.plot([vertices[a][0],vertices[b][0]],[vertices[a][1],vertices[b][1]],
            color="#cc0000",linestyle="--",lw=0.9,alpha=0.50,zorder=8)
for a,b in valid_edges:
    ax.plot([vertices[a][0],vertices[b][0]],[vertices[a][1],vertices[b][1]],
            color="#1a6b1a",lw=1.8,alpha=0.90,zorder=9)

for i,(lon,lat) in enumerate(vertices):
    ax.scatter(lon,lat,s=110,c="#111111",zorder=10,edgecolors="white",linewidths=0.9)
    ax.annotate(str(i+1),(lon,lat),fontsize=6,ha="center",va="center",
                color="white",fontweight="bold",zorder=11)

PLACE_SIZE={"town":220,"suburb":180,"village":140,"hamlet":100}
for v in villages:
    sz=PLACE_SIZE.get(v["type"],140)
    ax.scatter(v["lon"],v["lat"],s=sz*3,c="none",
               edgecolors="#ff6600",linewidths=2.2,zorder=11,marker="o")
    ax.scatter(v["lon"],v["lat"],s=sz*0.6,c="#ff6600",zorder=12,marker="*")
    ax.annotate(v["name"],(v["lon"],v["lat"]),xytext=(5,6),
                textcoords="offset points",fontsize=8,fontweight="bold",
                color="#cc4400",
                bbox=dict(boxstyle="round,pad=0.2",fc="white",
                          ec="#ff6600",lw=0.8,alpha=0.85),zorder=13)

cb = plt.colorbar(im, ax=ax, shrink=0.40, pad=0.01, aspect=16)
cb.set_label("Yangın Hassasiyeti", fontsize=9, rotation=270, labelpad=14)
cb.set_ticks([0,1,2,3,4,5])
cb.set_ticklabels(["0\nSu/Yapı","1\nOtlak","2","3\nMaki","4","5\nOrman"])

handles = [
    mpatches.Patch(facecolor="#9ecae1",ec="#555",lw=0.5,label="Deniz"),
    mpatches.Patch(facecolor="#2171b5",ec="#555",lw=0.5,label="Göl"),
    mpatches.Patch(facecolor="#7ecbc8",ec="#555",lw=0.5,label="Sulak alan"),
    plt.Line2D([0],[0],color="#0066cc",lw=2,  label="Nehir / Kanal"),
    plt.Line2D([0],[0],color="#2196f3",lw=1.2,label="Dere"),
    mpatches.Patch(facecolor="#b0b0b0",ec="#555",lw=0.5,label="Yapı / Çıplak"),
    mpatches.Patch(facecolor="#f5deb3",ec="#555",lw=0.5,label="Tarım"),
    plt.Line2D([0],[0],color="#1a6b1a",lw=2,  label="Aktif edge (yangın geçer)"),
    plt.Line2D([0],[0],color="#cc0000",lw=1,ls="--",label="Pasif edge (bariyer)"),
    plt.Line2D([0],[0],marker="o",color="w",markerfacecolor="#111111",
               markersize=8,label="Vertex"),
    plt.Line2D([0],[0],marker="*",color="w",markerfacecolor="#ff6600",
               markersize=10,label="Köy (öncelikli koruma)"),
]
ax.legend(handles=handles,loc="upper left",fontsize=8.5,framealpha=0.95,
          edgecolor="#aaa",title="Açıklama",title_fontsize=9,
          bbox_to_anchor=(1.01,1),borderaxespad=0)

nv,nb = len(valid_edges),len(blocked_edges)
ax.set_title(
    f"Köyceğiz–Marmaris ~589 km²  |  {len(vertices)} vertex  |  "
    f"{nv} aktif, {nb} pasif edge\n"
    f"Engeller (doğal koşullar): Su · Nehir · Tarım · Yapı · Ormansız Alan · Köy",
    fontsize=11, fontweight="bold", pad=10)
ax.set_xlabel("Boylam",fontsize=10)
ax.set_ylabel("Enlem", fontsize=10)
ax.set_xlim(WEST,EAST); ax.set_ylim(SOUTH,NORTH)
ax.tick_params(labelsize=9)
ax.grid(color="white",alpha=0.15,lw=0.4)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
print(f"    Kaydedildi: {OUT}", flush=True)
plt.show()
print("=== BITTI ===", flush=True)
