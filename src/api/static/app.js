"use strict";
/* FarmaExpress · interfaz web. Consume la misma API REST que Swagger (/docs). Sin dependencias. */
const ROLES = {CAJERO: "Cajero", RESPONSABLE_FARMACIA: "Responsable de farmacia", ALMACEN: "Almacén", COMPRAS: "Compras"};
const DEFAULT_ID = {CAJERO: "C1", RESPONSABLE_FARMACIA: "RF1", ALMACEN: "A1", COMPRAS: "K1"};
const S = {user: {id: "C1", rol: "CAJERO"}, cat: null, view: "inicio", cart: [], suc: ""};
const MXN = new Intl.NumberFormat("es-MX", {style: "currency", currency: "MXN"});
const money = v => MXN.format(Number(v));
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const $ = (s, r = document) => r.querySelector(s);
const legible = s => String(s ?? "").replace(/_/g, " ").toLowerCase().replace(/^./, c => c.toUpperCase());

/* ---------- vistas por rol ---------- */
const VISTAS = [
  {id: "inicio", ico: "🏠", nombre: "Inicio", roles: null},
  {id: "ventas", ico: "🛒", nombre: "Ventas", roles: ["CAJERO", "RESPONSABLE_FARMACIA"]},
  {id: "catalogo", ico: "💊", nombre: "Productos y lotes", roles: null},
  {id: "retiros", ico: "⚠️", nombre: "Retiro de lotes", roles: ["RESPONSABLE_FARMACIA", "ALMACEN"]},
  {id: "ajustes", ico: "📋", nombre: "Diferencias y ajustes", roles: ["RESPONSABLE_FARMACIA", "ALMACEN"]},
  {id: "reposicion", ico: "📦", nombre: "Reposición", roles: ["RESPONSABLE_FARMACIA", "ALMACEN", "COMPRAS"]},
  {id: "especiales", ico: "🔒", nombre: "Ventas especiales", roles: ["CAJERO", "RESPONSABLE_FARMACIA"]},
  {id: "reportes", ico: "📊", nombre: "Reportes", roles: ["RESPONSABLE_FARMACIA", "ALMACEN", "COMPRAS"]},
  {id: "auditoria", ico: "🕵️", nombre: "Auditoría", roles: ["RESPONSABLE_FARMACIA"]},
];
const permitida = v => !v.roles || v.roles.includes(S.user.rol);

/* ---------- API ---------- */
async function api(method, path, body) {
  const opt = {method, headers: {"X-User-Id": S.user.id, "X-User-Role": S.user.rol}};
  if (body) {
    const f = new URLSearchParams();
    for (const [k, v] of Object.entries(body)) if (v !== undefined && v !== null && v !== "") f.append(k, v);
    opt.body = f;
    opt.headers["Content-Type"] = "application/x-www-form-urlencoded";
  }
  const r = await fetch(path, opt);
  let data = null;
  try { data = await r.json(); } catch (_) { /* sin cuerpo */ }
  if (!r.ok) throw {status: r.status, data};
  return data;
}
function errMsg(e) {
  const d = (e && e.data) || {};
  const det = d.detalle || d.detail || "";
  switch (e && e.status) {
    case 400: return "Revisa los datos: " + (d.errores || []).map(x => `${String(x.campo).replace("body.", "")}: ${x.mensaje}`).join("; ");
    case 401: return "Falta identificarte: escribe tu usuario y elige tu rol arriba.";
    case 403: return "Tu rol no puede realizar esta acción. " + det;
    case 404: return "No se encontró lo que buscas. " + det;
    case 409: return "Esa acción no es posible en el estado actual. " + det;
    case 422: return (d.explicacion && d.explicacion.length) ? d.explicacion.join(" ") : det;
    default: return "No se pudo completar la operación. Intenta de nuevo.";
  }
}
function toast(kind, titulo, texto) {
  const t = document.createElement("div");
  t.className = "toast " + kind;
  t.innerHTML = `<b>${esc(titulo)}</b>${esc(texto || "")}`;
  $("#toasts").append(t);
  setTimeout(() => t.remove(), kind === "ok" ? 6000 : 9000);
}
const ok = r => toast("ok", "Listo", r && r.mensaje);
const fail = e => toast("err", "No se pudo", errMsg(e));
async function run(fn) { try { return await fn(); } catch (e) { if (e && e.status) fail(e); else { console.error(e); toast("err", "Error", "Ocurrió un problema inesperado."); } return null; } }

/* ---------- componentes ---------- */
const CLASIF = {NORMAL: ["b-ok", "Vigente"], PROXIMO_A_CADUCAR: ["b-warn", "Próximo a caducar"], CRITICO: ["b-crit", "Crítico"], CADUCADO: ["b-bad", "Caducado"]};
const badgeCad = c => { const [k, t] = CLASIF[c] || ["b-mute", legible(c)]; return `<span class="badge ${k}">${t}</span>`; };
const ESTADO = {EN_PROCESO: ["b-info", "En proceso"], COMPLETADA: ["b-ok", "Completada"], CANCELADA: ["b-mute", "Cancelada"],
  PENDIENTE: ["b-warn", "Pendiente"], AUTORIZADO: ["b-info", "Autorizado"], APLICADO: ["b-ok", "Aplicado"], RECHAZADO: ["b-bad", "Rechazado"],
  REGISTRADO: ["b-info", "Registrado"], EN_EJECUCION: ["b-warn", "En ejecución"], EJECUTADO: ["b-ok", "Ejecutado"],
  PENDIENTE_REVISION: ["b-warn", "Pendiente de revisión"], CONFIRMADA: ["b-ok", "Confirmada"], RECHAZADA: ["b-bad", "Rechazada"],
  EN_REVISION: ["b-warn", "En revisión"], ENVIADA: ["b-ok", "Enviada"], AUTORIZADA: ["b-ok", "Autorizada"], ACEPTADA: ["b-ok", "Aceptada"]};
const badge = e => { const [k, t] = ESTADO[e] || ["b-mute", legible(e)]; return `<span class="badge ${k}">${t}</span>`; };
const CATEG = {VENTA_LIBRE: "Venta libre", RECETA_SIMPLE: "Con receta", CONTROLADO: "Controlado"};
const prodDe = id => (S.cat.productos.find(p => p.id === id) || {});
const lotesDe = id => (prodDe(id).lotes || []);
const opt = (v, t, sel) => `<option value="${esc(v)}"${sel ? " selected" : ""}>${esc(t)}</option>`;
const tabla = (cols, filas, vacio = "Sin registros.") => filas.length
  ? `<div class="tw"><table><thead><tr>${cols.map(c => `<th${c.num ? ' class="num"' : ""}>${esc(c.t)}</th>`).join("")}</tr></thead><tbody>${filas.join("")}</tbody></table></div>`
  : `<div class="empty">${esc(vacio)}</div>`;
const sucOpts = sel => (S.cat?.sucursales || []).map(s => opt(s, s, s === sel)).join("");

/* ---------- modal genérico con formulario ---------- */
function cerrarModal() { $("#modalRoot").innerHTML = ""; }
function modal(titulo, html, {wide = false} = {}) {
  $("#modalRoot").innerHTML = `<div class="overlay" role="dialog" aria-modal="true" aria-label="${esc(titulo)}"><div class="modal${wide ? " wide" : ""}"><h2><span>${esc(titulo)}</span><button class="x" data-x aria-label="Cerrar">×</button></h2><div id="mBody">${html}</div></div></div>`;
  $("#modalRoot .overlay").addEventListener("click", e => { if (e.target.classList.contains("overlay") || e.target.dataset.x !== undefined) cerrarModal(); });
  return $("#mBody");
}
function campo(f) {
  const id = "f_" + f.name, req = f.required === false ? "" : " required";
  const hint = f.hint ? `<small>${esc(f.hint)}</small>` : "";
  if (f.type === "checkbox") return `<div class="field chk"><input type="checkbox" id="${id}" name="${f.name}"><label for="${id}">${esc(f.label)}</label></div>`;
  let ctrl;
  if (f.type === "select") ctrl = `<select id="${id}" name="${f.name}"${req}>${f.options.join("")}</select>`;
  else if (f.type === "producto") ctrl = `<select id="${id}" name="${f.name}"${req} data-producto>${S.cat.productos.filter(p => p.habilitado !== false || f.todos).map(p => opt(p.id, `${p.id} · ${p.descripcion}`, p.id === f.value)).join("")}</select>`;
  else if (f.type === "lote") ctrl = `<select id="${id}" name="${f.name}" data-lote="${f.of}" data-solo-vendibles="${f.vendibles ? 1 : 0}"></select>`;
  else if (f.type === "textarea") ctrl = `<textarea id="${id}" name="${f.name}" rows="3"${req} placeholder="${esc(f.ph || "")}">${esc(f.value || "")}</textarea>`;
  else ctrl = `<input id="${id}" name="${f.name}" type="${f.type || "text"}"${req} value="${esc(f.value ?? "")}" placeholder="${esc(f.ph || "")}"${f.min !== undefined ? ` min="${f.min}"` : ""}>`;
  return `<div class="field"><label for="${id}">${esc(f.label)}</label>${ctrl}${hint}</div>`;
}
function enlazarLotes(form) {
  const prods = form.querySelectorAll("select[data-producto]");
  const pintar = () => form.querySelectorAll("select[data-lote]").forEach(sel => {
    const p = form.querySelector(`[name="${sel.dataset.lote}"]`);
    const soloV = sel.dataset.soloVendibles === "1";
    const prev = sel.value;
    const lotes = lotesDe(p ? p.value : "").filter(l => !soloV || l.vendible);
    sel.innerHTML = (soloV ? "" : `<option value="">Sin especificar</option>`) + lotes.map(l => `<option value="${esc(l.id)}">${esc(l.id)} · ${CLASIF[l.clasificacion]?.[1] || l.clasificacion}${l.retirado ? " · RETIRADO" : ""}</option>`).join("");
    if (lotes.some(l => l.id === prev)) sel.value = prev;
  });
  prods.forEach(p => p.addEventListener("change", pintar));
  pintar();
}
function formulario(titulo, campos, etiqueta, enviar, intro = "") {
  const body = modal(titulo, `${intro ? `<p class="muted">${intro}</p>` : ""}<form id="mForm">${campos.map(campo).join("")}<div class="row end"><button type="button" class="btn ghost" data-x>Cancelar</button><button class="btn" type="submit">${esc(etiqueta)}</button></div></form>`);
  const form = $("#mForm", body);
  enlazarLotes(form);
  form.addEventListener("submit", async ev => {
    ev.preventDefault();
    const v = {};
    for (const el of form.elements) if (el.name) v[el.name] = el.type === "checkbox" ? (el.checked ? "true" : "false") : el.value.trim();
    const btn = form.querySelector("[type=submit]"); btn.disabled = true;
    const mio = $("#modalRoot .overlay");
    const r = await run(() => enviar(v));
    btn.disabled = false;
    if (r !== null && r !== undefined && $("#modalRoot .overlay") === mio) cerrarModal();
  });
  body.querySelectorAll("[data-x]").forEach(b => b.addEventListener("click", cerrarModal));
}
const confirmar = (titulo, texto, etiqueta, accion, peligro) => {
  const b = modal(titulo, `<p>${texto}</p><div class="row end"><button class="btn ghost" data-x>Cancelar</button><button class="btn ${peligro ? "danger" : ""}" id="mOk">${esc(etiqueta)}</button></div>`);
  b.querySelector("[data-x]").addEventListener("click", cerrarModal);
  $("#mOk", b).addEventListener("click", async () => {
    const mio = $("#modalRoot .overlay");
    const r = await run(accion);
    if (r !== null && r !== undefined && $("#modalRoot .overlay") === mio) cerrarModal();
  });
};

/* ---------- catálogo / sesión ---------- */
async function cargarCatalogo() { S.cat = await api("GET", "/catalogo"); return S.cat; }
function guardarUsuario() { try { localStorage.setItem("fx_user", JSON.stringify(S.user)); } catch (_) { /* sin storage */ } }
function leerUsuario() { try { const u = JSON.parse(localStorage.getItem("fx_user")); if (u && ROLES[u.rol] && u.id) S.user = u; } catch (_) { /* sin storage */ } }

function pintarNav() {
  $("#nav").innerHTML = VISTAS.filter(permitida).map(v => `<button data-v="${v.id}" class="${S.view === v.id ? "on" : ""}"><span class="ico">${v.ico}</span>${v.nombre}</button>`).join("");
  $("#uId").value = S.user.id; $("#uRol").value = S.user.rol;
}
async function ir(id) {
  const v = VISTAS.find(x => x.id === id && permitida(x)) || VISTAS[0];
  S.view = v.id; pintarNav(); $("#nav").classList.remove("open");
  const main = $("#main"); main.innerHTML = `<p class="muted">Cargando…</p>`;
  await run(async () => { await cargarCatalogo(); await RENDER[v.id](main); return 1; });
  main.focus({preventScroll: true});
}
const titulo = (t, s) => `<h1>${esc(t)}</h1><p class="sub">${esc(s)}</p>`;

/* ================= INICIO ================= */
const RENDER = {};
RENDER.inicio = async main => {
  const lotes = S.cat.productos.flatMap(p => p.lotes.map(l => ({...l, producto: p})));
  const cuenta = c => lotes.filter(l => l.clasificacion === c && !l.retirado).length;
  const stock = lotes.reduce((a, l) => a + l.existencias.reduce((x, e) => x + e.cantidad, 0), 0);
  let ventas = [];
  if (["CAJERO", "RESPONSABLE_FARMACIA"].includes(S.user.rol)) ventas = await api("GET", "/ventas");
  const alertas = lotes.filter(l => ["CADUCADO", "CRITICO", "PROXIMO_A_CADUCAR"].includes(l.clasificacion) || l.retirado)
    .sort((a, b) => a.dias_restantes - b.dias_restantes);
  const accesos = VISTAS.filter(v => permitida(v) && v.id !== "inicio");
  main.innerHTML = `${titulo(`Hola, ${S.user.id}`, `Estás trabajando como ${ROLES[S.user.rol]}. Elige un módulo del menú o usa los accesos rápidos.`)}
  <div class="grid g4" style="margin-bottom:16px">
    <div class="card kpi"><b>${S.cat.productos.length}</b><span>Productos en catálogo</span></div>
    <div class="card kpi"><b>${stock}</b><span>Piezas en existencia (todas las sucursales)</span></div>
    <div class="card kpi"><b>${cuenta("CRITICO") + cuenta("CADUCADO")}</b><span>Lotes críticos o caducados</span></div>
    <div class="card kpi"><b>${ventas.filter(v => v.estado === "EN_PROCESO").length}</b><span>Ventas en proceso</span></div>
  </div>
  <div class="grid g2">
    <section class="card"><h2>Atención en caducidad y retiros</h2>
      ${tabla([{t: "Lote"}, {t: "Producto"}, {t: "Estado"}, {t: "Días", num: 1}],
        alertas.map(l => `<tr><td class="mono">${esc(l.id)}</td><td>${esc(l.producto.descripcion)}</td><td>${l.retirado ? '<span class="badge b-bad">Retirado</span>' : badgeCad(l.clasificacion)}</td><td class="num">${l.dias_restantes}</td></tr>`),
        "Todos los lotes están vigentes.")}
    </section>
    <section class="card"><h2>Accesos rápidos</h2><div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(160px,1fr))">
      ${accesos.map(v => `<button class="btn ghost" data-v="${v.id}">${v.ico} ${v.nombre}</button>`).join("")}</div>
      <p class="muted" style="margin-top:16px">La documentación técnica de la API (Swagger) sigue disponible en <a href="/docs" target="_blank" rel="noopener">/docs</a>.</p>
    </section>
  </div>`;
};

/* ================= VENTAS ================= */
RENDER.ventas = async main => {
  const lista = await api("GET", "/ventas");
  if (!S.suc) S.suc = S.cat.sucursales[0] || "SUC-01";
  main.innerHTML = `${titulo("Ventas", "Registra una venta, agrégale productos y ciérrala. Al completarla se valida la vigencia, la receta y las existencias.")}
  <div class="split">
    <section class="card"><h2>Nueva venta</h2>
      <div class="field"><label for="vSuc">Sucursal</label><select id="vSuc">${sucOpts(S.suc)}</select></div>
      <form id="vAdd">
        <div class="field"><label for="vProd">Producto</label><select id="vProd" name="producto_id" data-producto>${S.cat.productos.filter(p => p.habilitado).map(p => opt(p.id, `${p.descripcion} · ${money(p.precio)}${p.requiere_receta ? " · receta" : ""}`)).join("")}</select></div>
        <div class="field"><label for="vLote">Lote</label><select id="vLote" name="lote_id" data-lote="producto_id" data-solo-vendibles="1"></select><small>Solo se listan lotes vendibles.</small></div>
        <div class="field"><label for="vCant">Cantidad</label><input id="vCant" name="cantidad" type="number" min="1" value="1" required></div>
        <button class="btn ghost" type="submit">＋ Agregar al carrito</button>
      </form>
      <hr style="border:0;border-top:1px solid var(--line);margin:16px 0">
      <h3>Carrito</h3><div id="vCart"></div>
    </section>
    <section class="card"><h2>Ventas recientes</h2>
      <div class="field" style="max-width:240px"><label for="vFiltro">Mostrar</label><select id="vFiltro"><option value="">Todas</option><option value="EN_PROCESO">En proceso</option><option value="COMPLETADA">Completadas</option><option value="CANCELADA">Canceladas</option></select></div>
      <div id="vLista"></div></section>
  </div>`;
  enlazarLotes($("#vAdd"));
  const pintarLista = () => {
    const f = $("#vFiltro").value;
    const rows = lista.filter(v => !f || v.estado === f).map(v => `<tr class="click" data-venta="${esc(v.id)}"><td class="mono">${esc(v.id)}</td><td>${esc(v.sucursal_id)}</td><td>${v.lineas.length}</td><td class="num">${money(v.total)}</td><td>${badge(v.estado)}</td></tr>`);
    $("#vLista").innerHTML = tabla([{t: "Folio"}, {t: "Sucursal"}, {t: "Productos"}, {t: "Total", num: 1}, {t: "Estado"}], rows, "Aún no hay ventas. Crea la primera desde el panel de la izquierda.");
  };
  $("#vFiltro").addEventListener("change", pintarLista); pintarLista();
  $("#vSuc").addEventListener("change", e => { S.suc = e.target.value; });
  const pintarCart = () => {
    const total = S.cart.reduce((a, i) => a + i.cantidad * Number(prodDe(i.producto_id).precio || 0), 0);
    $("#vCart").innerHTML = S.cart.length
      ? `<ul style="list-style:none;padding:0;margin:0 0 10px">${S.cart.map((i, n) => `<li class="row" style="justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--line)"><span>${i.cantidad} × ${esc(prodDe(i.producto_id).descripcion)}${i.lote_id ? ` <span class="chip">${esc(i.lote_id)}</span>` : ""}</span><button class="btn ghost sm" data-quita="${n}" aria-label="Quitar">Quitar</button></li>`).join("")}</ul>
         <div class="row" style="justify-content:space-between"><span class="muted">Total estimado</span><span class="total">${money(total)}</span></div>
         <div class="row" style="margin-top:10px"><button class="btn" id="vCrear">Registrar venta</button><button class="btn ghost" id="vVaciar">Vaciar</button></div>`
      : `<div class="empty">El carrito está vacío.</div>`;
    $("#vQuita")?.remove();
    document.querySelectorAll("[data-quita]").forEach(b => b.addEventListener("click", () => { S.cart.splice(Number(b.dataset.quita), 1); pintarCart(); }));
    $("#vVaciar")?.addEventListener("click", () => { S.cart = []; pintarCart(); });
    $("#vCrear")?.addEventListener("click", async () => {
      const r = await run(async () => {
        const [p, ...resto] = S.cart;
        let v = await api("POST", "/ventas", {sucursal_id: S.suc, producto_id: p.producto_id, cantidad: p.cantidad, lote_id: p.lote_id});
        for (const i of resto) v = await api("POST", `/ventas/${v.id}/lineas`, {producto_id: i.producto_id, cantidad: i.cantidad, lote_id: i.lote_id});
        return v;
      });
      if (r) { S.cart = []; toast("ok", "Venta registrada", `Folio ${r.id}. ${r.mensaje}`); await ir("ventas"); abrirVenta(r.id); }
    });
  };
  pintarCart();
  $("#vAdd").addEventListener("submit", e => {
    e.preventDefault();
    const f = new FormData(e.target);
    S.cart.push({producto_id: f.get("producto_id"), cantidad: Number(f.get("cantidad")), lote_id: f.get("lote_id")});
    pintarCart();
  });
};

async function abrirVenta(id) {
  const v = await run(() => api("GET", `/ventas/${encodeURIComponent(id)}`));
  if (!v) return;
  const rf = S.user.rol === "RESPONSABLE_FARMACIA", enProceso = v.estado === "EN_PROCESO";
  const body = modal(`Venta ${v.id}`, `
    <div class="kv"><div><span>Estado</span>${badge(v.estado)}</div><div><span>Sucursal</span>${esc(v.sucursal_id)}</div><div><span>Cajero</span>${esc(v.cajero_id)}</div><div><span>Total</span><b class="total">${money(v.total)}</b></div></div>
    ${tabla([{t: "Producto"}, {t: "Lote"}, {t: "Cantidad", num: 1}, {t: "Precio", num: 1}, {t: "Subtotal", num: 1}],
      v.lineas.map(l => `<tr><td>${esc(prodDe(l.producto_id).descripcion || l.producto_id)}${l.requiere_receta ? ' <span class="badge b-info">Receta</span>' : ""}</td><td class="mono">${esc(l.lote_id || "—")}</td><td class="num">${l.cantidad}</td><td class="num">${money(l.precio_unitario)}</td><td class="num">${money(l.subtotal)}</td></tr>`))}
    ${v.receta ? `<div class="alert info" style="margin-top:12px"><b>Receta ${esc(v.receta.folio)}</b> · ${esc(v.receta.medico)} · resultado: ${esc(legible(v.receta.resultado))}${v.receta.revisada_por ? ` (revisó ${esc(v.receta.revisada_por)})` : ""}</div>`
      : (v.requiere_receta && enProceso ? '<div class="alert warn" style="margin-top:12px">Esta venta incluye productos con receta: el responsable de farmacia debe revisarla antes de completar.</div>' : "")}
    ${v.observaciones ? `<p><b>Observaciones:</b> ${esc(v.observaciones)}</p>` : ""}
    ${v.correcciones.length ? `<h3>Correcciones</h3><ul>${v.correcciones.map(c => `<li>${esc(c.campo)}: «${esc(c.valor_anterior ?? c.anterior ?? "")}» → «${esc(c.valor_nuevo ?? c.nuevo ?? "")}» · ${esc(c.motivo)}</li>`).join("")}</ul>` : ""}
    <div class="row" style="margin-top:16px">
      ${enProceso ? `<button class="btn" data-a="completar">Completar venta</button><button class="btn ghost" data-a="linea">Agregar producto</button>
        ${rf && v.requiere_receta ? '<button class="btn ghost" data-a="receta">Revisar receta</button>' : ""}
        ${rf ? '<button class="btn ghost" data-a="sustituir">Autorizar sustitución</button><button class="btn ghost" data-a="sinalt">Sin alternativa</button>' : ""}
        <button class="btn danger" data-a="cancelar">Cancelar venta</button>` : ""}
      ${v.estado === "COMPLETADA" && rf ? '<button class="btn ghost" data-a="corregir">Corregir observaciones</button>' : ""}
    </div>`, {wide: true});
  const recargar = async () => { cerrarModal(); if (S.view === "ventas") await ir("ventas"); await abrirVenta(v.id); };
  const U = `/ventas/${encodeURIComponent(v.id)}`;
  const acciones = {
    completar: () => confirmar("Completar venta", `Se cobrarán <b>${money(v.total)}</b> y se descontará el inventario. ¿Continuar?`, "Completar y cobrar", async () => { const r = await api("POST", `${U}/completar`, {}); ok(r); await recargar(); return r; }),
    cancelar: () => formulario("Cancelar venta", [{name: "motivo", label: "Motivo (opcional)", type: "textarea", required: false}], "Cancelar venta", async d => { const r = await api("POST", `${U}/cancelar`, d); ok(r); setTimeout(recargar, 0); return r; }),
    linea: () => formulario("Agregar producto", [{name: "producto_id", label: "Producto", type: "producto"}, {name: "lote_id", label: "Lote", type: "lote", of: "producto_id", vendibles: true}, {name: "cantidad", label: "Cantidad", type: "number", min: 1, value: 1}], "Agregar", async d => { const r = await api("POST", `${U}/lineas`, d); ok(r); setTimeout(recargar, 0); return r; }),
    receta: () => formulario("Revisión de receta", [
      {name: "folio", label: "Folio de la receta"}, {name: "medico", label: "Médico"}, {name: "cedula_medico", label: "Cédula profesional"},
      {name: "nombre_paciente", label: "Paciente"}, {name: "fecha_emision", label: "Fecha de emisión", type: "date", value: new Date().toISOString().slice(0, 10)},
      {name: "resultado", label: "Resultado", type: "select", options: ["ACEPTADA", "INCOMPLETA", "VENCIDA", "NO_ACEPTADA"].map(x => opt(x, legible(x)))}], "Registrar revisión",
      async d => { const r = await api("POST", `${U}/receta/revision`, d); ok(r); setTimeout(recargar, 0); return r; }),
    sustituir: () => formulario("Autorizar sustitución", [
      {name: "producto_solicitado", label: "Producto solicitado", type: "select", options: v.lineas.map(l => opt(l.producto_id, `${l.producto_id} · ${prodDe(l.producto_id).descripcion || ""}`))},
      {name: "alternativa_id", label: "Alternativa", type: "producto"}, {name: "lote_id", label: "Lote de la alternativa", type: "lote", of: "alternativa_id", vendibles: true},
      {name: "motivo", label: "Motivo", type: "textarea"}], "Autorizar", async d => { const r = await api("POST", `${U}/sustituciones`, d); ok(r); setTimeout(recargar, 0); return r; }),
    sinalt: () => formulario("Sin alternativa aceptada", [
      {name: "producto_solicitado", label: "Producto solicitado", type: "select", options: v.lineas.map(l => opt(l.producto_id, `${l.producto_id} · ${prodDe(l.producto_id).descripcion || ""}`))},
      {name: "motivo", label: "Motivo", type: "textarea"}], "Registrar", async d => { const r = await api("POST", `${U}/sustituciones/rechazo`, d); ok(r); return r; }),
    corregir: () => formulario("Corregir datos descriptivos", [
      {name: "campo", label: "Dato", type: "select", options: [opt("observaciones", "Observaciones")]}, {name: "nuevo_valor", label: "Nuevo valor"},
      {name: "motivo", label: "Motivo de la corrección"}, {name: "solicitante_id", label: "Quién lo solicita", value: v.cajero_id}], "Registrar corrección",
      async d => { const r = await api("POST", `${U}/correcciones`, d); ok(r); setTimeout(recargar, 0); return r; },
      "Solo se pueden corregir datos descriptivos. Los productos, cantidades y el total no cambian."),
  };
  body.querySelectorAll("[data-a]").forEach(b => b.addEventListener("click", () => acciones[b.dataset.a]()));
}

/* ================= CATÁLOGO ================= */
RENDER.catalogo = async main => {
  main.innerHTML = `${titulo("Productos y lotes", "Existencias por sucursal y estado de caducidad de cada lote.")}
  <div class="row" style="margin-bottom:14px"><input id="cBusca" type="search" placeholder="Buscar producto…" aria-label="Buscar producto" style="min-width:260px"></div><div id="cLista" class="grid g2"></div>`;
  const pintar = () => {
    const q = $("#cBusca").value.toLowerCase();
    $("#cLista").innerHTML = S.cat.productos.filter(p => !q || (p.id + p.descripcion).toLowerCase().includes(q)).map(p => `<article class="card prod">
      <header><div><h2 style="margin:0">${esc(p.descripcion)}</h2><span class="muted mono">${esc(p.id)}</span></div>
      <div style="text-align:right"><b>${money(p.precio)}</b><br><span class="badge ${p.categoria === "VENTA_LIBRE" ? "b-mute" : "b-info"}">${CATEG[p.categoria] || p.categoria}</span>${p.habilitado ? "" : ' <span class="badge b-bad">No habilitado</span>'}</div></header>
      <div class="lotes">${p.lotes.map(l => `<div class="lote"><div class="top"><span><b class="mono">${esc(l.id)}</b> · vence ${esc(l.fecha_caducidad)} (${l.dias_restantes} días)</span>${l.retirado ? '<span class="badge b-bad">Retirado</span>' : badgeCad(l.clasificacion)}</div>
        <div class="chips">${l.existencias.map(e => `<span class="chip">${esc(e.sucursal_id)}: <b>${e.cantidad}</b></span>`).join("") || '<span class="muted">Sin existencias</span>'}</div>
        <div class="row"><span class="muted">${l.vendible ? "Se puede vender" : "No se puede vender"}</span>${S.user.rol === "RESPONSABLE_FARMACIA" && !l.retirado ? `<button class="btn ghost sm" data-retiro="${esc(l.id)}">Registrar retiro</button>` : ""}</div></div>`).join("") || '<div class="muted">Sin lotes registrados.</div>'}</div></article>`).join("") || '<div class="empty">Sin resultados.</div>';
  };
  $("#cBusca").addEventListener("input", pintar); pintar();
};
const registrarRetiro = (lote) => formulario("Registrar retiro de lote", [
  {name: "lote_id", label: "Lote", type: "select", options: S.cat.productos.flatMap(p => p.lotes.filter(l => !l.retirado).map(l => opt(l.id, `${l.id} · ${p.descripcion}`, l.id === lote)))},
  {name: "motivo", label: "Motivo del retiro", type: "textarea", ph: "Ej. alerta sanitaria"}], "Registrar retiro",
  async d => { const r = await api("POST", `/lotes/${encodeURIComponent(d.lote_id)}/retiro`, {motivo: d.motivo}); ok(r); setTimeout(() => ir(S.view), 0); return r; },
  "El lote quedará bloqueado para la venta en todas las sucursales.");

/* ================= REPORTES (listas) ================= */
async function reporte(tipo, params = {}) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v));
  return api("GET", `/reportes/${tipo}${q.toString() ? "?" + q : ""}`);
}

/* ================= RETIROS ================= */
RENDER.retiros = async main => {
  const r = await reporte("retiros");
  main.innerHTML = `${titulo("Retiro de lotes", "Un retiro bloquea el lote en todas las sucursales. Almacén registra las unidades localizadas y retiradas.")}
  ${S.user.rol === "RESPONSABLE_FARMACIA" ? '<div class="row" style="margin-bottom:14px"><button class="btn" data-retiro="">＋ Registrar retiro</button></div>' : ""}
  <section class="card">${tabla([{t: "Retiro"}, {t: "Lote"}, {t: "Producto"}, {t: "Estado"}, {t: "Localizadas", num: 1}, {t: "Retiradas", num: 1}, {t: "En tránsito", num: 1}, {t: ""}],
    r.filas.map(x => `<tr><td class="mono">${esc(x.retiro_id)}</td><td class="mono">${esc(x.lote_id)}</td><td>${esc(prodDe(x.producto_id).descripcion || x.producto_id)}</td><td>${badge(x.estado)}</td><td class="num">${x.identificadas}</td><td class="num">${x.retiradas}</td><td class="num">${x.en_transito_pendiente}</td>
      <td class="row">${x.estado !== "EJECUTADO" ? `<button class="btn ghost sm" data-ejec="${esc(x.retiro_id)}">Registrar unidades</button><button class="btn ghost sm" data-conc="${esc(x.retiro_id)}">Concluir</button>` : ""}</td></tr>`),
    "No hay retiros registrados.")}</section>`;
};

/* ================= DIFERENCIAS Y AJUSTES ================= */
RENDER.ajustes = async main => {
  const [dif, aj] = await Promise.all([reporte("diferencias"), reporte("ajustes")]);
  const rf = S.user.rol === "RESPONSABLE_FARMACIA";
  main.innerHTML = `${titulo("Diferencias y ajustes de inventario", "Registra la diferencia del conteo, investígala y solicita un ajuste. Lo autoriza un responsable distinto de quien lo solicita.")}
  <div class="row" style="margin-bottom:14px"><button class="btn" id="nDif">＋ Registrar diferencia</button></div>
  <section class="card" style="margin-bottom:16px"><h2>Diferencias</h2>${tabla([{t: "Diferencia"}, {t: "Sucursal"}, {t: "Producto"}, {t: "Lote"}, {t: "Sistema", num: 1}, {t: "Físico", num: 1}, {t: "Dif.", num: 1}, {t: "Estado"}, {t: ""}],
    dif.filas.map(d => `<tr><td class="mono">${esc(d.diferencia_id)}</td><td>${esc(d.sucursal_id)}</td><td>${esc(prodDe(d.producto_id).descripcion || d.producto_id)}${d.prioritaria ? ' <span class="badge b-crit">Prioritaria</span>' : ""}</td><td class="mono">${esc(d.lote_id || "—")}</td><td class="num">${d.cantidad_registrada}</td><td class="num">${d.cantidad_fisica}</td><td class="num">${d.delta}</td><td>${badge(d.estado)}</td>
      <td class="row"><button class="btn ghost sm" data-inv="${esc(d.diferencia_id)}">Investigar</button><button class="btn ghost sm" data-saj="${esc(d.diferencia_id)}">Solicitar ajuste</button></td></tr>`),
    "No hay diferencias registradas.")}</section>
  <section class="card"><h2>Ajustes</h2>${tabla([{t: "Ajuste"}, {t: "Producto"}, {t: "Sucursal"}, {t: "Antes", num: 1}, {t: "Después", num: 1}, {t: "Estado"}, {t: "Solicitó"}, {t: "Autorizó"}, {t: ""}],
    aj.filas.map(a => `<tr><td class="mono">${esc(a.ajuste_id)}</td><td>${esc(prodDe(a.producto_id).descripcion || a.producto_id)}</td><td>${esc(a.sucursal_id)}</td><td class="num">${a.cantidad_anterior}</td><td class="num">${a.cantidad_nueva}</td><td>${badge(a.estado)}</td><td>${esc(a.ejecutor_id)}</td><td>${esc(a.autorizador_id || "—")}</td>
      <td class="row">${a.estado === "PENDIENTE" && rf ? `<button class="btn sm" data-aut="${esc(a.ajuste_id)}">Autorizar</button><button class="btn ghost sm" data-rech="${esc(a.ajuste_id)}">Rechazar</button>` : ""}${a.estado === "AUTORIZADO" ? `<button class="btn sm" data-apl="${esc(a.ajuste_id)}">Aplicar</button>` : ""}</td></tr>`),
    "No hay ajustes.")}</section>`;
  $("#nDif").addEventListener("click", () => formulario("Registrar diferencia", [
    {name: "sucursal_id", label: "Sucursal", type: "select", options: S.cat.sucursales.map(s => opt(s, s))},
    {name: "producto_id", label: "Producto", type: "producto", todos: true}, {name: "lote_id", label: "Lote", type: "lote", of: "producto_id"},
    {name: "cantidad_fisica", label: "Cantidad contada físicamente", type: "number", min: 0}, {name: "prioritaria", label: "Marcar como prioritaria", type: "checkbox"}], "Registrar",
    async d => { const r = await api("POST", "/diferencias", d); ok(r); setTimeout(() => ir("ajustes"), 0); return r; }, "El inventario no cambia hasta que se aplique un ajuste autorizado."));
};

/* ================= REPOSICIÓN ================= */
RENDER.reposicion = async main => {
  const r = await reporte("solicitudes");
  main.innerHTML = `${titulo("Reposición", "Almacén reporta necesidades; el responsable de farmacia las confirma y envía la solicitud a Compras.")}
  ${["ALMACEN", "RESPONSABLE_FARMACIA"].includes(S.user.rol) ? '<div class="row" style="margin-bottom:14px"><button class="btn" id="nSol">＋ Nueva solicitud de compra</button></div>' : ""}
  <section class="card">${tabla([{t: "Solicitud"}, {t: "Sucursal"}, {t: "Estado"}, {t: "Necesidades", num: 1}, {t: "Confirmadas", num: 1}, {t: "Envío"}],
    r.filas.map(s => `<tr class="click" data-sol="${esc(s.solicitud_id)}"><td class="mono">${esc(s.solicitud_id)}</td><td>${esc(s.sucursal_id)}</td><td>${badge(s.estado)}</td><td class="num">${s.necesidades}</td><td class="num">${s.confirmadas}</td><td>${esc(s.fecha_envio ? s.fecha_envio.slice(0, 10) : "—")}</td></tr>`),
    "No hay solicitudes de compra.")}</section>`;
  $("#nSol")?.addEventListener("click", () => formulario("Nueva solicitud de compra", [{name: "sucursal_id", label: "Sucursal", type: "select", options: S.cat.sucursales.map(s => opt(s, s))}], "Crear",
    async d => { const x = await api("POST", "/solicitudes-compra", d); toast("ok", "Solicitud creada", x.mensaje); setTimeout(() => ir("reposicion"), 0); setTimeout(() => abrirSolicitud(x.id), 50); return x; }));
};
async function abrirSolicitud(id) {
  const s = await run(() => api("GET", `/solicitudes-compra/${encodeURIComponent(id)}`));
  if (!s) return;
  const rf = S.user.rol === "RESPONSABLE_FARMACIA", alm = ["ALMACEN", "RESPONSABLE_FARMACIA"].includes(S.user.rol);
  const U = `/solicitudes-compra/${encodeURIComponent(s.id)}`;
  const body = modal(`Solicitud ${s.id}`, `<div class="kv"><div><span>Estado</span>${badge(s.estado)}</div><div><span>Sucursal</span>${esc(s.sucursal_id)}</div><div><span>Solicitante</span>${esc(s.solicitante_id || "—")}</div></div>
    ${tabla([{t: "Producto"}, {t: "Motivo"}, {t: "Solicitada", num: 1}, {t: "Confirmada", num: 1}, {t: "Estado"}, {t: ""}],
      s.necesidades.map(n => `<tr><td>${esc(prodDe(n.producto_id).descripcion || n.producto_id)}</td><td>${esc(legible(n.motivo))}</td><td class="num">${n.cantidad_requerida}</td><td class="num">${n.cantidad_confirmada ?? "—"}</td><td>${badge(n.estado)}</td>
        <td class="row">${rf && n.estado === "PENDIENTE_REVISION" && s.estado !== "ENVIADA" ? `<button class="btn sm" data-conf="${esc(n.id)}">Confirmar</button><button class="btn ghost sm" data-rech="${esc(n.id)}">Rechazar</button>` : ""}</td></tr>`), "Aún no hay necesidades.")}
    ${s.estado === "ENVIADA" ? `<h3 style="margin-top:14px">Enviado a Compras</h3><ul>${s.lineas_a_comprar.map(l => `<li>${esc(l.cantidad ?? l.cantidad_confirmada ?? "")} × ${esc(prodDe(l.producto_id).descripcion || l.producto_id)}</li>`).join("")}</ul>` : ""}
    <div class="row" style="margin-top:14px">${alm && s.estado !== "ENVIADA" ? '<button class="btn ghost" data-a="nec">＋ Agregar necesidad</button>' : ""}${rf && s.estado !== "ENVIADA" ? '<button class="btn" data-a="enviar">Enviar a Compras</button>' : ""}</div>`, {wide: true});
  const recargar = () => { cerrarModal(); abrirSolicitud(s.id); if (S.view === "reposicion") ir("reposicion"); };
  body.querySelectorAll("[data-conf]").forEach(b => b.addEventListener("click", () => formulario("Confirmar necesidad", [{name: "cantidad", label: "Cantidad confirmada", type: "number", min: 1, required: false, hint: "Déjalo vacío para confirmar la cantidad solicitada."}], "Confirmar", async d => { const r = await api("POST", `${U}/necesidades/${encodeURIComponent(b.dataset.conf)}/confirmar`, d); ok(r); setTimeout(recargar, 0); return r; })));
  body.querySelectorAll("[data-rech]").forEach(b => b.addEventListener("click", () => confirmar("Rechazar necesidad", "No se enviará a Compras.", "Rechazar", async () => { const r = await api("POST", `${U}/necesidades/${encodeURIComponent(b.dataset.rech)}/rechazar`, {}); ok(r); setTimeout(recargar, 0); return r; }, true)));
  body.querySelector('[data-a="nec"]')?.addEventListener("click", () => formulario("Reportar necesidad", [{name: "producto_id", label: "Producto", type: "producto", todos: true}, {name: "cantidad", label: "Cantidad", type: "number", min: 1},
    {name: "motivo", label: "Motivo", type: "select", options: ["FALTANTE", "EXISTENCIA_BAJA", "CADUCADO"].map(x => opt(x, legible(x)))}], "Registrar", async d => { const r = await api("POST", `${U}/necesidades`, d); ok(r); setTimeout(recargar, 0); return r; }));
  body.querySelector('[data-a="enviar"]')?.addEventListener("click", () => confirmar("Enviar a Compras", "Se enviará solo lo confirmado; lo demás quedará fuera.", "Enviar", async () => { const r = await api("POST", `${U}/enviar`, {}); ok(r); setTimeout(recargar, 0); return r; }));
}

/* ================= VENTAS ESPECIALES ================= */
RENDER.especiales = async main => {
  const regs = await api("GET", "/registros-especiales");
  main.innerHTML = `${titulo("Ventas especiales", "Ventas con receta. Los datos personales de pacientes y médicos solo los ve el responsable de farmacia, y cada consulta queda auditada.")}
  ${S.user.rol !== "RESPONSABLE_FARMACIA" ? '<div class="alert info">Con tu rol no se muestran datos personales de pacientes ni médicos.</div>' : ""}
  <section class="card">${tabla([{t: "Venta"}, {t: "Sucursal"}, {t: "Receta"}, {t: "Resultado"}, {t: "Revisó"}, {t: "Paciente"}, {t: "Médico"}],
    regs.map(r => `<tr class="click" data-esp="${esc(r.venta_id)}"><td class="mono">${esc(r.venta_id)}</td><td>${esc(r.sucursal_id)}</td><td>${esc(r.folio_receta || "—")}</td><td>${r.resultado_revision ? badge(r.resultado_revision) : "—"}</td><td>${esc(r.revisada_por || "—")}</td><td>${r.datos_personales_visibles ? esc(r.nombre_paciente || "—") : '<span class="muted">Restringido</span>'}</td><td>${r.datos_personales_visibles ? esc(r.nombre_medico || "—") : '<span class="muted">Restringido</span>'}</td></tr>`),
    "Todavía no hay ventas con receta registradas.")}</section>`;
};
async function abrirEspecial(id) {
  const r = await run(() => api("GET", `/registros-especiales/${encodeURIComponent(id)}`));
  if (!r) return;
  modal(`Registro de venta ${r.venta_id}`, `<div class="alert info">${esc(r.mensaje)}</div><div class="kv"><div><span>Estado de la venta</span>${badge(r.estado_venta)}</div><div><span>Sucursal</span>${esc(r.sucursal_id)}</div><div><span>Receta</span>${esc(r.folio_receta || "—")}</div><div><span>Resultado</span>${r.resultado_revision ? badge(r.resultado_revision) : "—"}</div><div><span>Revisó</span>${esc(r.revisada_por || "—")}</div><div><span>Fecha de emisión</span>${esc(r.fecha_emision || "—")}</div>
    ${r.datos_personales_visibles ? `<div><span>Paciente</span>${esc(r.nombre_paciente || "—")}</div><div><span>Médico</span>${esc(r.nombre_medico || "—")}</div><div><span>Cédula</span>${esc(r.cedula_medico || "—")}</div>` : ""}</div>
    <h3>Sustituciones</h3>${tabla([{t: "Estado"}, {t: "Solicitado"}, {t: "Alternativa"}, {t: "Motivo"}, {t: "Responsable"}], r.sustituciones.map(s => `<tr><td>${badge(s.estado)}</td><td>${esc(s.producto_solicitado)}</td><td>${esc(s.alternativa || "—")}</td><td>${esc(s.motivo)}</td><td>${esc(s.responsable_id)}</td></tr>`), "Sin sustituciones.")}`, {wide: true});
}

/* ================= REPORTES ================= */
const TIPOS = {caducidad: "Caducidad", retiros: "Retiros de lote", diferencias: "Diferencias de inventario", ajustes: "Ajustes", solicitudes: "Solicitudes de compra", ventas_especiales: "Ventas especiales"};
RENDER.reportes = async main => {
  main.innerHTML = `${titulo("Reportes", "Consulta con filtros y exporta el resultado a CSV.")}
  <form class="card" id="rForm"><div class="grid g4">
    <div class="field"><label for="rTipo">Reporte</label><select id="rTipo" name="tipo">${Object.entries(TIPOS).map(([k, v]) => opt(k, v)).join("")}</select></div>
    <div class="field"><label for="rSuc">Sucursal</label><select id="rSuc" name="sucursal_id"><option value="">Todas</option>${sucOpts("")}</select></div>
    <div class="field"><label for="rProd">Producto</label><select id="rProd" name="producto_id"><option value="">Todos</option>${S.cat.productos.map(p => opt(p.id, p.descripcion)).join("")}</select></div>
    <div class="field"><label for="rEst">Estado</label><input id="rEst" name="estado" placeholder="Ej. CADUCADO, PENDIENTE"></div>
    <div class="field"><label for="rLote">Lote</label><input id="rLote" name="lote_id" placeholder="Ej. LOT-001"></div>
    <div class="field"><label for="rDesde">Desde</label><input id="rDesde" name="desde" type="date"></div>
    <div class="field"><label for="rHasta">Hasta</label><input id="rHasta" name="hasta" type="date"></div>
    <div class="field" style="justify-content:flex-end"><button class="btn" type="submit">Generar reporte</button></div></div></form>
  <section class="card" style="margin-top:16px" id="rOut"><div class="empty">Elige un reporte y pulsa «Generar reporte».</div></section>`;
  let ultimo = null;
  $("#rForm").addEventListener("submit", async e => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    const tipo = f.tipo; delete f.tipo;
    const r = await run(() => reporte(tipo, f));
    if (!r) return;
    ultimo = r;
    const cols = r.filas.length ? Object.keys(r.filas[0]) : [];
    $("#rOut").innerHTML = `<div class="row" style="justify-content:space-between;margin-bottom:10px"><h2 style="margin:0">${esc(TIPOS[tipo])} · ${r.total} registro(s)</h2>${r.filas.length ? '<button class="btn ghost sm" id="rCsv">Exportar CSV</button>' : ""}</div>
      ${tabla(cols.map(c => ({t: legible(c)})), r.filas.map(x => `<tr>${cols.map(c => `<td>${esc(Array.isArray(x[c]) ? x[c].join(", ") : (typeof x[c] === "boolean" ? (x[c] ? "Sí" : "No") : x[c] ?? "—"))}</td>`).join("")}</tr>`), "No hay registros con esos filtros.")}`;
    $("#rCsv")?.addEventListener("click", () => {
      const csv = [cols.join(","), ...ultimo.filas.map(x => cols.map(c => `"${String(Array.isArray(x[c]) ? x[c].join(";") : x[c] ?? "").replace(/"/g, '""')}"`).join(","))].join("\n");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob(["﻿" + csv], {type: "text/csv;charset=utf-8"}));
      a.download = `reporte_${tipo}.csv`; a.click(); URL.revokeObjectURL(a.href);
    });
  });
};

/* ================= AUDITORÍA ================= */
RENDER.auditoria = async main => {
  main.innerHTML = `${titulo("Auditoría", "Historial de acciones: quién hizo qué, cuándo y con qué datos.")}
  <form class="row card" id="aForm" style="margin-bottom:16px"><div class="field" style="margin:0"><label for="aEnt">Folio o código</label><input id="aEnt" name="entidad_id" placeholder="Ej. VTA-1A2B3C4D"></div><div class="field" style="margin:0"><label for="aAcc">Acción</label><input id="aAcc" name="accion" placeholder="Ej. COMPLETAR_VENTA"></div><div class="field" style="margin:0;justify-content:flex-end"><button class="btn" type="submit">Filtrar</button></div></form>
  <section class="card" id="aOut"></section>`;
  const cargar = async () => {
    const q = new URLSearchParams(Object.entries(Object.fromEntries(new FormData($("#aForm")))).filter(([, v]) => v));
    const rows = await run(() => api("GET", "/auditoria" + (q.toString() ? "?" + q : "")));
    if (!rows) return;
    $("#aOut").innerHTML = tabla([{t: "Fecha"}, {t: "Usuario"}, {t: "Acción"}, {t: "Entidad"}, {t: "Folio"}, {t: "Antes"}, {t: "Después"}],
      rows.slice().reverse().map(a => `<tr><td>${esc(String(a.fecha).replace("T", " ").slice(0, 19))}</td><td>${esc(a.usuario)}</td><td>${esc(a.accion)}</td><td>${esc(a.entidad)}</td><td class="mono">${esc(a.entidad_id)}</td><td>${esc(a.antes)}</td><td>${esc(a.despues)}</td></tr>`), "Sin movimientos con esos filtros.");
  };
  $("#aForm").addEventListener("submit", e => { e.preventDefault(); cargar(); });
  cargar();
};

/* ================= eventos globales ================= */
document.addEventListener("click", async e => {
  const t = e.target.closest("[data-v],[data-venta],[data-retiro],[data-ejec],[data-conc],[data-inv],[data-saj],[data-aut],[data-rech],[data-apl],[data-sol],[data-esp]");
  if (!t || t.closest("#modalRoot") && !(t.dataset.venta || t.dataset.sol)) {
    if (!t) return;
    if (t.closest("#modalRoot") && (t.dataset.rech !== undefined && t.closest("form, table") && t.closest("#mBody"))) return; // los maneja la propia vista
    if (t.closest("#modalRoot")) return;
  }
  const d = t.dataset;
  if (d.v) return ir(d.v);
  if (d.venta) return abrirVenta(d.venta);
  if (d.sol) return abrirSolicitud(d.sol);
  if (d.esp) return abrirEspecial(d.esp);
  if (t.closest("#modalRoot")) return;
  if (d.retiro !== undefined) return registrarRetiro(d.retiro);
  const rec = () => ir(S.view);
  if (d.ejec) return formulario("Registrar unidades del retiro", [{name: "sucursal_id", label: "Sucursal", type: "select", options: S.cat.sucursales.map(s => opt(s, s))}, {name: "identificadas", label: "Unidades localizadas", type: "number", min: 0}, {name: "retiradas", label: "Unidades retiradas físicamente", type: "number", min: 0}], "Registrar", async v => { const r = await api("POST", `/retiros/${encodeURIComponent(d.ejec)}/ejecuciones`, v); ok(r); setTimeout(rec, 0); return r; });
  if (d.conc) return confirmar("Concluir retiro", "Solo se puede concluir cuando no quedan unidades en tránsito pendientes.", "Concluir retiro", async () => { const r = await api("POST", `/retiros/${encodeURIComponent(d.conc)}/concluir`, {}); ok(r); setTimeout(rec, 0); return r; });
  if (d.inv) return formulario("Investigar diferencia", [{name: "causa", label: "Causa identificada", type: "textarea", required: false, hint: "Déjala vacía si aún está pendiente de aclaración."}, {name: "evidencia", label: "Evidencia", type: "textarea", required: false}], "Registrar investigación", async v => { const r = await api("POST", `/diferencias/${encodeURIComponent(d.inv)}/investigacion`, v); ok(r); setTimeout(rec, 0); return r; });
  if (d.saj) return formulario("Solicitar ajuste", [{name: "motivo", label: "Motivo del ajuste", type: "textarea"}], "Solicitar ajuste", async v => { const r = await api("POST", "/ajustes", {diferencia_id: d.saj, motivo: v.motivo}); ok(r); setTimeout(rec, 0); return r; }, "Debe estar investigada con causa y evidencia.");
  if (d.aut) return confirmar("Autorizar ajuste", "Una vez autorizado, Almacén podrá aplicarlo.", "Autorizar", async () => { const r = await api("POST", `/ajustes/${encodeURIComponent(d.aut)}/autorizar`, {}); ok(r); setTimeout(rec, 0); return r; });
  if (d.rech) return confirmar("Rechazar ajuste", "La existencia no cambiará.", "Rechazar", async () => { const r = await api("POST", `/ajustes/${encodeURIComponent(d.rech)}/rechazar`, {}); ok(r); setTimeout(rec, 0); return r; }, true);
  if (d.apl) return confirmar("Aplicar ajuste", "Esto modifica la existencia registrada.", "Aplicar ajuste", async () => { const r = await api("POST", `/ajustes/${encodeURIComponent(d.apl)}/aplicar`, {}); ok(r); setTimeout(rec, 0); return r; });
});
$("#nav").addEventListener("click", e => { const b = e.target.closest("[data-v]"); if (b) ir(b.dataset.v); });
$("#menuBtn").addEventListener("click", () => $("#nav").classList.toggle("open"));
$("#uRol").addEventListener("change", e => {
  const previo = DEFAULT_ID[S.user.rol];
  S.user.rol = e.target.value;
  if (!S.user.id || S.user.id === previo) S.user.id = DEFAULT_ID[S.user.rol];
  guardarUsuario(); ir(S.view);
});
$("#uId").addEventListener("change", e => { S.user.id = e.target.value.trim() || DEFAULT_ID[S.user.rol]; guardarUsuario(); ir(S.view); });
leerUsuario(); pintarNav(); ir("inicio");
