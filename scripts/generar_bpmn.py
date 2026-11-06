"""Genera los diagramas BPMN 2.0 del equipo (.bpmn con DI + .svg) a partir de una descripción
declarativa. Uso:  python scripts/generar_bpmn.py   ->  docs/architecture/bpmn/PM-xx_*.{bpmn,svg}

El .bpmn se abre en bpmn.io / Camunda Modeler / draw.io; el .svg es para el reporte."""
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "architecture" / "bpmn"
COL_W, LANE_H, HEAD = 175, 250, 44
SUBY = {1: 72, 0: 125, 2: 185}
TW, TH, GW, ER = 150, 68, 54, 18


class Proceso:
    def __init__(self, pid, titulo, lanes, nodos, flujos, desc=""):
        self.pid, self.titulo, self.lanes, self.desc = pid, titulo, lanes, desc
        self.nodos = {n[0]: dict(id=n[0], t=n[1], label=n[2], lane=n[3], col=n[4],
                                 sub=n[5] if len(n) > 5 else 0) for n in nodos}
        self.flujos = [(f + ("",))[:4] for f in flujos]
        self._geom()

    def _geom(self):
        for n in self.nodos.values():
            n["x"] = HEAD + n["col"] * COL_W + COL_W / 2
            n["y"] = self.lanes.index(n["lane"]) * LANE_H + SUBY[n["sub"]] + 30
            w, h = {"start": (2 * ER, 2 * ER), "end": (2 * ER, 2 * ER), "inter": (2 * ER, 2 * ER),
                    "gw": (GW, GW)}.get(n["t"], (TW, TH))
            n["w"], n["h"] = w, h
        self.ancho = HEAD + (max(n["col"] for n in self.nodos.values()) + 1) * COL_W + 20
        self.alto = len(self.lanes) * LANE_H + 60

    # ------------------------------ ruteo ortogonal ------------------------------
    def _mixto(self, nid):
        """Compuerta con salidas hacia arriba y hacia abajo: se rutean con codo lateral."""
        sy = self.nodos[nid]["y"]
        dest = [self.nodos[b]["y"] for a, b, _, _h in self.flujos if a == nid]
        return any(d > sy + 1 for d in dest) and any(d < sy - 1 for d in dest)

    def ruta(self, a, b, h=""):
        s, d = self.nodos[a], self.nodos[b]
        if s["t"] == "gw" and self._mixto(a):
            h = "h"
        sx, sy, dx, dy = s["x"], s["y"], d["x"], d["y"]
        der = lambda n: (n["x"] + n["w"] / 2, n["y"])        # noqa: E731
        izq = lambda n: (n["x"] - n["w"] / 2, n["y"])        # noqa: E731
        arr = lambda n: (n["x"], n["y"] - n["h"] / 2)        # noqa: E731
        aba = lambda n: (n["x"], n["y"] + n["h"] / 2)        # noqa: E731
        if d["col"] > s["col"]:
            if abs(sy - dy) < 1:
                return [der(s), izq(d)]
            if s["t"] == "gw" and h != "h":
                return [aba(s) if dy > sy else arr(s), (sx, dy), izq(d)]
            mid = izq(d)[0] - 22 if d["col"] - s["col"] > 1 else (der(s)[0] + izq(d)[0]) / 2
            return [der(s), (mid, sy), (mid, dy), izq(d)]
        if d["col"] == s["col"]:
            return [aba(s), arr(d)] if dy > sy else [arr(s), aba(d)]
        yt = min(arr(s)[1], arr(d)[1]) - 18
        return [arr(s), (sx, yt), (dx, yt), arr(d)]

    # ------------------------------ SVG ------------------------------
    def svg(self):
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.ancho}" height="{self.alto}" '
             f'viewBox="0 0 {self.ancho} {self.alto}" font-family="Arial, Helvetica, sans-serif">',
             '<defs><marker id="fl" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
             'markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker>'
             '</defs>', '<rect width="100%" height="100%" fill="#fff"/>',
             f'<text x="12" y="22" font-size="15" font-weight="bold">{escape(self.titulo)}</text>']
        for i, lane in enumerate(self.lanes):
            y = 30 + i * LANE_H
            fill = "#fafafa" if i % 2 == 0 else "#f3f6fb"
            o.append(f'<rect x="1" y="{y}" width="{self.ancho - 2}" height="{LANE_H}" fill="{fill}" '
                     'stroke="#222" stroke-width="1.2"/>')
            o.append(f'<rect x="1" y="{y}" width="{HEAD - 6}" height="{LANE_H}" fill="#e6ebf2" '
                     'stroke="#222" stroke-width="1.2"/>')
            o.append(f'<text transform="translate(24,{y + LANE_H / 2}) rotate(-90)" font-size="12" '
                     f'font-weight="bold" text-anchor="middle">{escape(lane)}</text>')
        for a, b, etq, h in self.flujos:
            pts = self.ruta(a, b, h)
            o.append('<polyline fill="none" stroke="#222" stroke-width="1.4" marker-end="url(#fl)" '
                     f'points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in pts)}"/>')
            if etq:
                (x1, y1), (_x2, y2) = pts[0], pts[1]
                if len(pts) == 4 and pts[1][0] == pts[2][0] and abs(y1 - pts[3][1]) > 1:
                    x1, y1 = pts[1][0] - 4, (pts[1][1] + pts[2][1]) / 2
                    o.append(f'<text x="{x1 + 10:.0f}" y="{y1 + 4:.0f}" font-size="10.5" '
                             f'font-weight="bold" fill="#8a1c1c">{escape(etq)}</text>')
                    continue
                tx, ty = (x1 + 6, y1 - 6) if abs(y1 - y2) < 1 else (x1 + 6, y1 + (14 if y2 > y1 else -6))
                o.append(f'<text x="{tx:.0f}" y="{ty:.0f}" font-size="10.5" font-weight="bold" '
                         f'fill="#8a1c1c">{escape(etq)}</text>')
        for n in self.nodos.values():
            o.append(self._svg_nodo(n))
        o.append("</svg>")
        return "\n".join(o)

    @staticmethod
    def _lineas(txt, ancho):
        return textwrap.wrap(txt, ancho) or [""]

    def _svg_nodo(self, n):
        x, y, w, h, t = n["x"], n["y"], n["w"], n["h"], n["t"]
        if t in ("task", "service"):
            fill = "#e8f1ff" if t == "service" else "#ffffff"
            s = (f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="9" '
                 f'fill="{fill}" stroke="#222" stroke-width="1.6"/>')
            ls = self._lineas(n["label"], 25)
            for i, ln in enumerate(ls):
                yy = y - (len(ls) - 1) * 6.5 + i * 13 + 4
                s += f'<text x="{x:.0f}" y="{yy:.0f}" font-size="10.5" text-anchor="middle">{escape(ln)}</text>'
            return s
        if t == "gw":
            pts = f"{x},{y - h / 2} {x + w / 2},{y} {x},{y + h / 2} {x - w / 2},{y}"
            s = (f'<polygon points="{pts}" fill="#fff8e1" stroke="#222" stroke-width="1.6"/>'
                 f'<path d="M{x - 9},{y - 9} L{x + 9},{y + 9} M{x + 9},{y - 9} L{x - 9},{y + 9}" '
                 'stroke="#222" stroke-width="2.4"/>')
            ls = self._lineas(n["label"], 24)
            sy = n["y"]
            dest = [self.nodos[b]["y"] for a, b, _, hh in self.flujos if a == n["id"]
                    and self.nodos[b]["col"] > n["col"]]
            abajo = any(d > sy + 1 for d in dest)
            arriba = any(d < sy - 1 for d in dest)
            anchor, xx = "middle", x
            if abajo or arriba and abajo:
                base = y - h / 2 - 8 - (len(ls) - 1) * 12
                if arriba:
                    anchor, xx = "end", x + 14
            else:
                base = y + h / 2 + 13
            for i, ln in enumerate(ls):
                s += (f'<text x="{xx:.0f}" y="{base + i * 12:.0f}" font-size="10.5" '
                      f'font-weight="bold" text-anchor="{anchor}">{escape(ln)}</text>')
            return s
        stroke = {"start": 2, "inter": 2, "end": 5}[t]
        col = {"start": "#2e7d32", "inter": "#b26a00", "end": "#b71c1c"}[t]
        s = f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{ER}" fill="#fff" stroke="{col}" stroke-width="{stroke}"/>'
        if t == "inter":
            s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{ER - 4}" fill="none" stroke="{col}" stroke-width="1.5"/>'
        ls = self._lineas(n["label"], 22)
        for i, ln in enumerate(ls):
            s += (f'<text x="{x:.0f}" y="{y + ER + 13 + i * 12:.0f}" font-size="10.5" '
                  f'text-anchor="middle">{escape(ln)}</text>')
        return s

    # ------------------------------ BPMN 2.0 XML ------------------------------
    def bpmn(self):
        tag = {"start": "startEvent", "end": "endEvent", "inter": "intermediateThrowEvent",
               "gw": "exclusiveGateway", "task": "userTask", "service": "serviceTask"}
        sal, ent = {}, {}
        for i, (a, b, _, _h) in enumerate(self.flujos):
            sal.setdefault(a, []).append(f"F{i}")
            ent.setdefault(b, []).append(f"F{i}")
        x = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" '
             'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
             'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
             'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
             f'id="Defs_{self.pid}" targetNamespace="https://farmaexpress.example/bpmn">',
             f'<process id="Proceso_{self.pid}" name="{escape(self.titulo)}" isExecutable="false">',
             f'<laneSet id="Lanes_{self.pid}">']
        for i, lane in enumerate(self.lanes):
            x.append(f'<lane id="Lane_{self.pid}_{i}" name="{escape(lane)}">')
            x += [f"<flowNodeRef>{n['id']}</flowNodeRef>" for n in self.nodos.values()
                  if n["lane"] == lane]
            x.append("</lane>")
        x.append("</laneSet>")
        for n in self.nodos.values():
            x.append(f'<{tag[n["t"]]} id="{n["id"]}" name="{escape(n["label"])}">')
            x += [f"<incoming>{f}</incoming>" for f in ent.get(n["id"], [])]
            x += [f"<outgoing>{f}</outgoing>" for f in sal.get(n["id"], [])]
            x.append(f'</{tag[n["t"]]}>')
        for i, (a, b, etq, _h) in enumerate(self.flujos):
            nm = f' name="{escape(etq)}"' if etq else ""
            x.append(f'<sequenceFlow id="F{i}"{nm} sourceRef="{a}" targetRef="{b}"/>')
        x += ["</process>", f'<bpmndi:BPMNDiagram id="Diag_{self.pid}">',
              f'<bpmndi:BPMNPlane id="Plane_{self.pid}" bpmnElement="Proceso_{self.pid}">']
        for i, _lane in enumerate(self.lanes):
            x.append(f'<bpmndi:BPMNShape id="S_L{i}" bpmnElement="Lane_{self.pid}_{i}" '
                     f'isHorizontal="true"><dc:Bounds x="0" y="{30 + i * LANE_H}" '
                     f'width="{self.ancho}" height="{LANE_H}"/></bpmndi:BPMNShape>')
        for n in self.nodos.values():
            x.append(f'<bpmndi:BPMNShape id="S_{n["id"]}" bpmnElement="{n["id"]}"><dc:Bounds '
                     f'x="{n["x"] - n["w"] / 2:.0f}" y="{n["y"] - n["h"] / 2:.0f}" '
                     f'width="{n["w"]}" height="{n["h"]}"/></bpmndi:BPMNShape>')
        for i, (a, b, _, h) in enumerate(self.flujos):
            x.append(f'<bpmndi:BPMNEdge id="E_F{i}" bpmnElement="F{i}">')
            x += [f'<di:waypoint x="{px:.0f}" y="{py:.0f}"/>' for px, py in self.ruta(a, b, h)]
            x.append("</bpmndi:BPMNEdge>")
        x += ["</bpmndi:BPMNPlane>", "</bpmndi:BPMNDiagram>", "</definitions>"]
        return "\n".join(x)


RF, ALM, SIS, CAJ = "Responsable de farmacia", "Almacén", "Sistema", "Cajero"
UA = "Usuario autorizado"


def procesos():
    p = []
    p.append(Proceso("PM-02", "PM-02 · Retiro y seguimiento de lotes (US03, US04)", [RF, ALM, SIS], [
        ("s", "start", "Retiro de lote confirmado", RF, 0),
        ("t1", "task", "Registrar retiro del lote y su motivo", RF, 1),
        ("t2", "service", "Marcar lote como retirado y bloquear su venta en todas las sucursales", SIS, 2),
        ("e1", "inter", "LoteRetirado", SIS, 3),
        ("t3", "task", "Identificar y separar físicamente las unidades afectadas", ALM, 4),
        ("t4", "task", "Registrar cantidades identificadas y retiradas por sucursal", ALM, 5),
        ("g1", "gw", "¿Retiradas ≤ identificadas?", SIS, 6),
        ("t6", "service", "Registrar ejecución: retiro EN_EJECUCION y unidades en tránsito pendientes", SIS, 7),
        ("g2", "gw", "¿Quedan unidades en tránsito pendientes?", SIS, 8),
        ("t7", "task", "Resolver unidades en tránsito (ubicar o confirmar)", ALM, 8, 1),
        ("t8", "task", "Concluir el retiro", RF, 9),
        ("t9", "service", "Retiro CONCLUIDO y registro de auditoría (RF-16)", SIS, 10),
        ("f", "end", "Retiro documentado", SIS, 11),
    ], [("s", "t1", ""), ("t1", "t2", ""), ("t2", "e1", ""), ("e1", "t3", ""), ("t3", "t4", ""),
        ("t4", "g1", ""), ("g1", "t6", "Sí"), ("g1", "t4", "No · 422, corregir"),
        ("t6", "g2", ""), ("g2", "t7", "Sí"), ("t7", "t4", "nueva ejecución"),
        ("g2", "t8", "No", "h"), ("t8", "t9", ""), ("t9", "f", "")]))
    p.append(Proceso("PM-03", "PM-03 · Consulta de existencias entre sucursales (US05)", [UA, SIS], [
        ("s", "start", "Se necesita conocer disponibilidad", UA, 0),
        ("t1", "task", "Buscar el producto", UA, 1),
        ("g1", "gw", "¿Usuario identificado?", SIS, 2),
        ("t2", "service", "Consultar existencias registradas por sucursal y lote", SIS, 3),
        ("t3", "service", "Mostrar cantidades; sin reservas ni transferencias", SIS, 4),
        ("t4", "task", "Decidir con la información registrada", UA, 5),
        ("f", "end", "Consulta atendida", UA, 6),
        ("x", "end", "Acceso denegado (401)", SIS, 3, 2),
    ], [("s", "t1", ""), ("t1", "g1", ""), ("g1", "t2", "Sí"), ("g1", "x", "No"), ("t2", "t3", ""),
        ("t3", "t4", ""), ("t4", "f", "")]))
    p.append(Proceso("PM-07", "PM-07 · Evaluación y autorización de sustitución (US10)", [CAJ, RF, SIS], [
        ("s", "start", "Producto solicitado requiere sustitución", CAJ, 0),
        ("t1", "task", "Solicitar evaluación de sustitución", CAJ, 1),
        ("t2", "task", "Evaluar alternativas disponibles", RF, 2),
        ("g1", "gw", "¿Acepta una alternativa?", RF, 3),
        ("t3", "task", "Autorizar sustitución con alternativa y motivo", RF, 4, 1),
        ("t4", "service", "Validar venta EN_PROCESO y alternativa habilitada; reemplazar línea", SIS, 5, 1),
        ("e1", "inter", "SustitucionAutorizada", SIS, 6, 1),
        ("t5", "task", "Continuar la venta con la alternativa", CAJ, 7, 1),
        ("t6", "task", "Registrar rechazo con motivo", RF, 4, 2),
        ("t7", "service", "Guardar decisión; la venta no cambia", SIS, 6, 2),
        ("e2", "inter", "SustitucionRechazada", SIS, 7, 2),
        ("t8", "task", "Informar al cliente: continuar sin sustituir o cancelar", CAJ, 8, 2),
        ("f1", "end", "Venta con sustitución", CAJ, 8, 1),
        ("f2", "end", "Sin sustitución", CAJ, 9, 2),
    ], [("s", "t1", ""), ("t1", "t2", ""), ("t2", "g1", ""), ("g1", "t3", "Sí"), ("g1", "t6", "No"),
        ("t3", "t4", ""), ("t4", "e1", ""), ("e1", "t5", ""), ("t5", "f1", ""),
        ("t6", "t7", ""), ("t7", "e2", ""), ("e2", "t8", ""), ("t8", "f2", "")]))
    p.append(Proceso("PM-08", "PM-08 · Registro y consulta de ventas especiales (US11, US12)", [RF, UA, SIS], [
        ("s", "start", "Venta con medicamento que requiere receta", RF, 0),
        ("t1", "task", "Revisar receta y capturar folio, médico, cédula, paciente, fecha y resultado", RF, 1),
        ("t2", "service", "Conservar el registro con el responsable de la revisión", SIS, 2),
        ("e1", "inter", "RecetaRevisada", SIS, 3),
        ("t3", "task", "Solicitar consulta del registro", UA, 4),
        ("g1", "gw", "¿Qué rol consulta?", SIS, 5, 1),
        ("t4", "service", "Mostrar registro completo y auditar la consulta", SIS, 6, 1),
        ("t5", "service", "Mostrar registro sin datos personales de paciente ni médico", SIS, 6, 2),
        ("t6", "task", "Recibir acceso denegado (403)", UA, 6),
        ("f1", "end", "Consulta completa", SIS, 7, 1),
        ("f2", "end", "Consulta restringida", SIS, 7, 2),
        ("f3", "end", "Sin acceso", UA, 7),
    ], [("s", "t1", ""), ("t1", "t2", ""), ("t2", "e1", ""), ("e1", "t3", ""), ("t3", "g1", ""),
        ("g1", "t4", "Responsable"), ("g1", "t5", "Cajero"), ("g1", "t6", "Almacén / Compras"),
        ("t4", "f1", ""), ("t5", "f2", ""), ("t6", "f3", "")]))
    p.append(Proceso("PM-09", "PM-09 · Investigación de diferencias de inventario (US15, US16)", [ALM, RF, SIS], [
        ("s", "start", "Conteo físico de un producto", ALM, 0),
        ("t1", "task", "Comparar existencia física con la registrada", ALM, 1),
        ("g1", "gw", "¿Las cantidades coinciden?", ALM, 2),
        ("x", "end", "Sin diferencia: no se registra", ALM, 3, 2),
        ("t2", "task", "Registrar sucursal, producto, lote, ambas cantidades y fecha", ALM, 3, 1),
        ("t3", "service", "Guardar diferencia SIN_INVESTIGAR; la existencia no cambia", SIS, 4),
        ("e1", "inter", "DiferenciaDeInventarioRegistrada", SIS, 5),
        ("t4", "task", "Revisar movimientos y evidencia disponible", RF, 6),
        ("g2", "gw", "¿Se identificó la causa?", RF, 7),
        ("t5", "task", "Documentar causa y evidencia", RF, 8, 1),
        ("t6", "service", "Estado CAUSA_IDENTIFICADA: diferencia ajustable", SIS, 9, 1),
        ("f1", "end", "Lista para ajuste (PM-10)", SIS, 10, 1),
        ("t7", "task", "Marcar PENDIENTE_ACLARACION", RF, 8, 2),
        ("t8", "service", "Conservar como pendiente; no ajustable", SIS, 10, 2),
        ("f2", "end", "Investigación pendiente", SIS, 11, 2),
    ], [("s", "t1", ""), ("t1", "g1", ""), ("g1", "x", "Sí"), ("g1", "t2", "No"), ("t2", "t3", ""),
        ("t3", "e1", ""), ("e1", "t4", ""), ("t4", "g2", ""), ("g2", "t5", "Sí"), ("g2", "t7", "No"),
        ("t5", "t6", ""), ("t6", "f1", ""), ("t7", "t8", ""), ("t8", "f2", "")]))
    p.append(Proceso("PM-10", "PM-10 · Autorización y ejecución de ajustes de inventario (US17)", [ALM, RF, SIS], [
        ("s", "start", "Diferencia con causa y evidencia", ALM, 0),
        ("t1", "task", "Solicitar ajuste indicando diferencia y motivo", ALM, 1),
        ("t2", "service", "Registrar ajuste PENDIENTE (cantidad anterior y nueva)", SIS, 2, 1),
        ("g0", "gw", "¿Diferencia ajustable?", SIS, 3, 1),
        ("x0", "end", "Solicitud rechazada (422)", SIS, 4, 2),
        ("t3", "task", "Revisar la evidencia y decidir", RF, 4),
        ("g1", "gw", "¿Evidencia suficiente?", RF, 5),
        ("t4", "task", "Rechazar el ajuste", RF, 6),
        ("x1", "end", "Ajuste RECHAZADO; existencia sin cambios", RF, 7),
        ("g2", "gw", "¿Autoriza un responsable distinto del ejecutor?", SIS, 6, 1),
        ("x2", "end", "Denegado (403): Almacén no autoriza su ajuste", SIS, 7, 2),
        ("t5", "service", "Registrar autorización: AUTORIZADO, autorizador y fecha", SIS, 7, 1),
        ("e1", "inter", "AjusteDeInventarioAutorizado", SIS, 8, 1),
        ("t6", "task", "Aplicar el ajuste autorizado", ALM, 9),
        ("g3", "gw", "¿Existencia sin cambios desde la diferencia?", SIS, 10, 1),
        ("x3", "end", "Aplicación rechazada (422)", SIS, 11, 2),
        ("t7", "service", "Actualizar existencia, marcar APLICADO y auditar", SIS, 11, 1),
        ("e2", "inter", "AjusteDeInventarioAplicado", SIS, 12, 1),
        ("f", "end", "Existencia ajustada con historial", SIS, 13, 1),
    ], [("s", "t1", ""), ("t1", "t2", ""), ("t2", "g0", ""), ("g0", "t3", "Sí"), ("g0", "x0", "No"),
        ("t3", "g1", ""), ("g1", "g2", "Sí"), ("g1", "t4", "No"), ("t4", "x1", ""),
        ("g2", "t5", "Sí"), ("g2", "x2", "No"), ("t5", "e1", ""), ("e1", "t6", ""),
        ("t6", "g3", ""), ("g3", "t7", "Sí"), ("g3", "x3", "No"), ("t7", "e2", ""), ("e2", "f", "")]))
    p.append(Proceso("PM-11", "PM-11 · Generación de reportes operativos (US18)", [UA, SIS], [
        ("s", "start", "Se requiere supervisar la operación", UA, 0),
        ("t1", "task", "Elegir tipo de reporte y filtros (sucursal, producto, lote, estado, periodo)", UA, 1),
        ("g1", "gw", "¿Rol permitido (responsable, Almacén, Compras)?", SIS, 2),
        ("x1", "end", "Acceso denegado (403)", SIS, 3, 2),
        ("g2", "gw", "¿Tipo de reporte válido?", SIS, 3, 1),
        ("x2", "end", "Reporte inválido (422)", SIS, 4, 2),
        ("t2", "service", "Consultar registros y aplicar los filtros que correspondan", SIS, 4, 1),
        ("t3", "service", "Presentar el reporte (sin datos personales en ventas especiales)", SIS, 5, 1),
        ("t4", "task", "Analizar la información y decidir", UA, 6),
        ("f", "end", "Supervisión realizada", UA, 7),
    ], [("s", "t1", ""), ("t1", "g1", ""), ("g1", "g2", "Sí"), ("g1", "x1", "No"), ("g2", "t2", "Sí"),
        ("g2", "x2", "No"), ("t2", "t3", ""), ("t3", "t4", ""), ("t4", "f", "")]))
    p.append(Proceso("PM-12", "PM-12 · Corrección de datos descriptivos de una venta completada (US14)", [UA, RF, SIS], [
        ("s", "start", "Se detecta un error descriptivo en una venta completada", UA, 0),
        ("t1", "task", "Solicitar corrección: campo, nuevo valor y motivo", UA, 1),
        ("g1", "gw", "¿Venta COMPLETADA y campo descriptivo?", SIS, 2),
        ("x1", "end", "Corrección rechazada; venta sin cambios", SIS, 3, 2),
        ("t2", "task", "Revisar y decidir la autorización", RF, 3),
        ("g2", "gw", "¿Autoriza la corrección?", RF, 4),
        ("x2", "end", "Corrección no aplicada", RF, 5, 1),
        ("t3", "service", "Conservar dato original, nuevo, motivo, fecha, ejecutor y autorizador", SIS, 5, 1),
        ("e1", "inter", "VentaCorregida", SIS, 6, 1),
        ("f", "end", "Venta corregida sin alterar su operación económica", SIS, 7, 1),
    ], [("s", "t1", ""), ("t1", "g1", ""), ("g1", "t2", "Sí"), ("g1", "x1", "No"), ("t2", "g2", ""),
        ("g2", "t3", "Sí"), ("g2", "x2", "No"), ("t3", "e1", ""), ("e1", "f", "")]))
    return p


NOMBRES = {"PM-02": "retiro_lotes", "PM-03": "consulta_existencias", "PM-07": "sustitucion",
           "PM-08": "ventas_especiales", "PM-09": "diferencias_inventario",
           "PM-10": "ajustes_inventario", "PM-11": "reportes", "PM-12": "correccion_venta"}


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for pr in procesos():
        base = DESTINO / f"{pr.pid}_{NOMBRES[pr.pid]}"
        base.with_suffix(".svg").write_text(pr.svg(), encoding="utf-8")
        base.with_suffix(".bpmn").write_text(pr.bpmn(), encoding="utf-8")
        print("OK", base.name)


if __name__ == "__main__":
    main()
