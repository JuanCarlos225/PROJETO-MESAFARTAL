"""Matchmaking logístico: KNN con distancia haversine sobre latitud/longitud."""
import numpy as np
from sklearn.neighbors import NearestNeighbors

RADIO_TIERRA_KM = 6371.0


def ongs_mas_cercanas(latitud, longitud, ongs, k=3):
    """Devuelve las k ONGs más cercanas ordenadas por distancia: [{'ong': dict, 'distancia_km': float}]."""
    ongs = [o for o in ongs if o.get("latitud") is not None and o.get("longitud") is not None]
    if not ongs:
        return []
    coords = np.radians([[o["latitud"], o["longitud"]] for o in ongs])
    k = min(k, len(ongs))
    knn = NearestNeighbors(n_neighbors=k, metric="haversine", algorithm="ball_tree").fit(coords)
    dist, idx = knn.kneighbors(np.radians([[latitud, longitud]]))
    return [{"ong": ongs[i], "distancia_km": round(float(d) * RADIO_TIERRA_KM, 2)}
            for d, i in zip(dist[0], idx[0])]
