"""Ejecuta casos_prueba.csv y transiciones_prueba.csv y escribe la evidencia en docs/evidencia/.

    python scripts/ejecutar_fixtures.py
"""
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.infrastructure.fixtures_csv import (  # noqa: E402
    cargar_paquete,
    ejecutar_caso,
    ejecutar_transicion,
)


def escribir(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:     # UTF-8 con BOM
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


def main(carpeta: Path = RAIZ / "tests" / "fixtures" / "docente",
         destino: Path = RAIZ / "docs" / "evidencia") -> tuple[list[dict], list[dict]]:
    paquete = cargar_paquete(carpeta)
    casos = [ejecutar_caso(paquete, c) for c in paquete.casos]
    transiciones = [ejecutar_transicion(paquete, t) for t in paquete.transiciones]
    escribir(destino / "casos_prueba_resultados.csv", casos)
    escribir(destino / "transiciones_resultados.csv", transiciones)
    print(f"{len(casos)} casos y {len(transiciones)} transiciones -> {destino}")
    return casos, transiciones


if __name__ == "__main__":
    main()
