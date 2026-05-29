# =====================================================================
#  ANDARIEGO  ✈️  — VISTA DE CLIENTE
#  El cliente se identifica/registra por documento, explora el catálogo,
#  crea reservas, ve SOLO sus reservas y paga. No ve a otros clientes.
# =====================================================================

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import oracledb

# =====================================================================
#  1. CONEXIÓN
# =====================================================================

@st.cache_resource
def _init_oracle():
    try:
        oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_26")
    except Exception:
        pass
    return True


def conectar():
    _init_oracle()
    return oracledb.connect(user="mateo", password="Cenicient4!!", dsn="adbg07_low")


def consultar(sql, params=None):
    conn = conectar()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def ejecutar_dml(sql, params=None):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute(sql, params or {})
        conn.commit()
    finally:
        cur.close()
        conn.close()


# Busca un cliente por documento; si no existe lo crea. Devuelve su id.
def obtener_o_crear_cliente(tipo_doc, num_doc, nombre, apellido, fecha_nac, pais_id,
                            email=None, telefono=None):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("""SELECT cliente_id FROM av_clientes
                       WHERE tipo_doc = :t AND num_doc = :n""",
                    {"t": tipo_doc, "n": num_doc})
        row = cur.fetchone()
        if row:
            return int(row[0]), False
        new_id = cur.var(oracledb.NUMBER)
        cur.execute("""INSERT INTO av_clientes
            (tipo_doc, num_doc, nombre, apellido, fecha_nacimiento, email, telefono, pais_id)
            VALUES (:t, :n, :nom, :ape, :fn, :em, :tel, :pid)
            RETURNING cliente_id INTO :id""",
            {"t": tipo_doc, "n": num_doc, "nom": nombre, "ape": apellido,
             "fn": fecha_nac, "em": email, "tel": telefono, "pid": pais_id, "id": new_id})
        conn.commit()
        return int(new_id.getvalue()[0]), True
    finally:
        cur.close()
        conn.close()


# Inserta la reserva completa (cabecera + pasajeros + servicios) en una transacción.
def registrar_reserva_completa(titular_id, pasajeros_ids, fecha_ini, fecha_fin,
                               vuelos, hospedajes, transportes):
    conn = conectar()
    cur = conn.cursor()
    try:
        monto = (sum(v["precio"] for v in vuelos)
                 + sum(h["precio_total"] for h in hospedajes)
                 + sum(t["precio"] for t in transportes))
        new_id = cur.var(oracledb.NUMBER)
        cur.execute("""INSERT INTO av_reservas
            (cliente_id, fecha_inicio_viaje, fecha_fin_viaje, monto_total, estado)
            VALUES (:cli, :ini, :fin, :m, 'ACTIVA')
            RETURNING reserva_id INTO :id""",
            {"cli": titular_id, "ini": fecha_ini, "fin": fecha_fin, "m": monto, "id": new_id})
        rid = int(new_id.getvalue()[0])

        for i, cli in enumerate(pasajeros_ids, start=1):
            cur.execute("""INSERT INTO av_reserva_pasajeros (reserva_id, num_pasajero, cliente_id)
                           VALUES (:r, :n, :c)""", {"r": rid, "n": i, "c": cli})
        for v in vuelos:
            cur.execute("""INSERT INTO av_reserva_vuelos (reserva_id, vuelo_id, precio_aplicado, estado)
                           VALUES (:r, :v, :p, 'ACTIVO')""",
                        {"r": rid, "v": v["id"], "p": v["precio"]})
        for h in hospedajes:
            cur.execute("""INSERT INTO av_reserva_hospedajes
                (reserva_id, habitacion_id, fecha_checkin, fecha_checkout, num_noches, precio_total, estado)
                VALUES (:r, :h, :ci, :co, :n, :p, 'ACTIVO')""",
                {"r": rid, "h": h["id"], "ci": h["checkin"], "co": h["checkout"],
                 "n": h["noches"], "p": h["precio_total"]})
        for t in transportes:
            cur.execute("""INSERT INTO av_reserva_transportes (reserva_id, transporte_id, precio_aplicado, estado)
                           VALUES (:r, :t, :p, 'ACTIVO')""",
                        {"r": rid, "t": t["id"], "p": t["precio"]})
        conn.commit()
        return rid, monto
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# =====================================================================
#  2. CONFIGURACIÓN Y ESTILOS
# =====================================================================

st.set_page_config(page_title="Andariego ✈️", page_icon="✈️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #FFF9F5; }
    .hero {
        background: linear-gradient(120deg, #13B5C7 0%, #FF6B5B 100%);
        padding: 28px 36px; border-radius: 18px; color: white; margin-bottom: 18px;
        box-shadow: 0 6px 24px rgba(255,107,91,0.20);
    }
    .hero h1 { color: white; margin: 0; font-size: 34px; }
    .hero p  { color: #FFF3EF; margin: 6px 0 0 0; font-size: 16px; }
    .stButton > button[kind="primary"] { background:#FF6B5B; border:none; border-radius:10px; font-weight:600; }
    .stButton > button[kind="primary"]:hover { background:#ff5340; }
    section[data-testid="stSidebar"] { background-color:#0B6E99; }
    section[data-testid="stSidebar"] * { color:#E8F6FA !important; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
#  3. IDENTIFICACIÓN / REGISTRO (login simple por documento)
# =====================================================================

for k in ["cliente_id", "cliente_nombre"]:
    if k not in st.session_state:
        st.session_state[k] = None

if st.session_state.cliente_id is None:
    st.markdown("""
        <div class="hero"><h1>Andariego ✈️</h1>
        <p>Tu próximo viaje empieza aquí. Identifícate o regístrate para reservar.</p></div>
    """, unsafe_allow_html=True)

    tab_login, tab_registro = st.tabs(["🔑 Ya soy cliente", "🆕 Registrarme"])

    # ----- Login -----
    with tab_login:
        c1, c2 = st.columns(2)
        td = c1.selectbox("Tipo de documento", ["CC", "CE", "TI", "PAS", "NIT"], key="lg_td")
        nd = c2.text_input("Número de documento", key="lg_nd")
        if st.button("Ingresar", type="primary"):
            res = consultar("""SELECT cliente_id, nombre, apellido FROM av_clientes
                               WHERE tipo_doc = :t AND num_doc = :n AND estado = 'ACTIVO'""",
                            {"t": td, "n": nd})
            if res.empty:
                st.error("No encontramos ese documento. Regístrate en la otra pestaña.")
            else:
                st.session_state.cliente_id = int(res.iloc[0]["CLIENTE_ID"])
                st.session_state.cliente_nombre = f"{res.iloc[0]['NOMBRE']} {res.iloc[0]['APELLIDO']}"
                st.rerun()

    # ----- Registro -----
    with tab_registro:
        paises = consultar("SELECT pais_id, nombre FROM av_paises ORDER BY nombre")
        c1, c2 = st.columns(2)
        r_td = c1.selectbox("Tipo de documento", ["CC", "CE", "TI", "PAS", "NIT"], key="rg_td")
        r_nd = c2.text_input("Número de documento", key="rg_nd")
        r_nom = c1.text_input("Nombre")
        r_ape = c2.text_input("Apellido")
        r_email = c1.text_input("Email")
        r_tel = c2.text_input("Teléfono")
        r_pais = c1.selectbox("País", paises["NOMBRE"].tolist(), key="rg_pais")
        r_fn = c2.date_input("Fecha de nacimiento", value=date(2000, 1, 1),
                             min_value=date(1920, 1, 1),
                             max_value=date.today() - timedelta(days=1))
        if st.button("Crear cuenta y entrar", type="primary"):
            if not (r_nd and r_nom and r_ape):
                st.warning("Documento, nombre y apellido son obligatorios.")
            else:
                pid = int(paises[paises["NOMBRE"] == r_pais]["PAIS_ID"].values[0])
                try:
                    cid, creado = obtener_o_crear_cliente(
                        r_td, r_nd, r_nom, r_ape, r_fn, pid,
                        r_email or None, r_tel or None)
                    st.session_state.cliente_id = cid
                    st.session_state.cliente_nombre = f"{r_nom} {r_ape}"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrarte: {e}")

    st.stop()  # No mostrar el resto de la app hasta identificarse


# =====================================================================
#  4. MENÚ (cliente ya identificado)
# =====================================================================

CID = st.session_state.cliente_id

st.sidebar.markdown(f"## ✈️ Andariego")
st.sidebar.caption(f"Hola, {st.session_state.cliente_nombre} 👋")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.cliente_id = None
    st.session_state.cliente_nombre = None
    st.rerun()
st.sidebar.divider()

pagina = st.sidebar.radio("Menú", [
    "🏠 Inicio",
    "🌍 Explorar destinos",
    "✈️ Vuelos",
    "🏨 Hoteles",
    "🚌 Transporte",
    "📝 Nueva reserva",
    "🔍 Mis reservas",
    "💳 Pagar",
])


# =====================================================================
#  5. INICIO
# =====================================================================

if pagina == "🏠 Inicio":
    st.markdown(f"""
        <div class="hero"><h1>¡Bienvenido, {st.session_state.cliente_nombre}! ✈️</h1>
        <p>Explora destinos, arma tu viaje y reserva en minutos.</p></div>
    """, unsafe_allow_html=True)
    mis = consultar("""SELECT COUNT(*) AS n FROM av_reservas WHERE cliente_id = :c""",
                    {"c": CID}).iloc[0]["N"]
    st.info(f"Tienes **{int(mis)}** reserva(s) registrada(s). Ve a 🔍 Mis reservas para verlas.")


# =====================================================================
#  6. EXPLORAR / VUELOS / HOTELES / TRANSPORTE (solo lectura)
# =====================================================================

elif pagina == "🌍 Explorar destinos":
    st.subheader("🌍 Explorar destinos")
    continentes = consultar("SELECT DISTINCT continente FROM av_paises ORDER BY continente")["CONTINENTE"].tolist()
    filtro = st.selectbox("Continente", ["TODOS"] + continentes)
    where = "" if filtro == "TODOS" else "WHERE p.continente = :c"
    params = None if filtro == "TODOS" else {"c": filtro}
    st.dataframe(consultar(f"""
        SELECT p.nombre AS "País", ci.nombre AS "Ciudad",
               h.nombre AS "Hotel", h.estrellas AS "★"
        FROM av_hoteles h
        JOIN av_ciudades ci ON h.ciudad_id = ci.ciudad_id
        JOIN av_paises p ON ci.pais_id = p.pais_id
        {where} ORDER BY p.nombre, ci.nombre
    """, params), use_container_width=True, hide_index=True)

elif pagina == "✈️ Vuelos":
    st.subheader("✈️ Vuelos disponibles")
    st.dataframe(consultar("""
        SELECT al.nombre AS "Aerolínea", v.num_vuelo AS "Vuelo",
               ao.codigo_iata AS "Origen", ad.codigo_iata AS "Destino",
               TO_CHAR(v.fecha_salida,'DD/MM/YYYY HH24:MI') AS "Salida",
               v.precio_base AS "Precio"
        FROM av_vuelos v
        JOIN av_aerolineas al ON v.aerolinea_id = al.aerolinea_id
        JOIN av_aeropuertos ao ON v.aeropuerto_origen_id = ao.aeropuerto_id
        JOIN av_aeropuertos ad ON v.aeropuerto_destino_id = ad.aeropuerto_id
        WHERE v.estado = 'PROGRAMADO' ORDER BY v.fecha_salida
    """), use_container_width=True, hide_index=True)

elif pagina == "🏨 Hoteles":
    st.subheader("🏨 Hoteles y habitaciones")
    st.dataframe(consultar("""
        SELECT h.nombre AS "Hotel", ci.nombre AS "Ciudad", h.estrellas AS "★",
               hab.tipo AS "Tipo", hab.capacidad AS "Cap.", hab.precio_noche AS "Precio/noche"
        FROM av_habitaciones hab
        JOIN av_hoteles h ON hab.hotel_id = h.hotel_id
        JOIN av_ciudades ci ON h.ciudad_id = ci.ciudad_id
        WHERE hab.estado = 'DISPONIBLE' ORDER BY h.nombre
    """), use_container_width=True, hide_index=True)

elif pagina == "🚌 Transporte":
    st.subheader("🚌 Transporte terrestre")
    st.dataframe(consultar("""
        SELECT t.tipo AS "Tipo", t.empresa AS "Empresa",
               co.nombre AS "Origen", cd.nombre AS "Destino",
               TO_CHAR(t.fecha_salida,'DD/MM/YYYY HH24:MI') AS "Salida", t.precio AS "Precio"
        FROM av_transportes_terrestres t
        JOIN av_ciudades co ON t.ciudad_origen_id = co.ciudad_id
        JOIN av_ciudades cd ON t.ciudad_destino_id = cd.ciudad_id
        WHERE t.estado = 'PROGRAMADO' ORDER BY t.fecha_salida
    """), use_container_width=True, hide_index=True)


# =====================================================================
#  7. NUEVA RESERVA (el cliente logueado es el titular)
# =====================================================================

elif pagina == "📝 Nueva reserva":
    st.subheader("📝 Nueva reserva")

    for key in ["rsv_vuelos", "rsv_hosp", "rsv_transp"]:
        if key not in st.session_state:
            st.session_state[key] = []

    st.markdown(f"**Titular:** {st.session_state.cliente_nombre} (tú)")

    # ---------- Acompañante (opcional, por documento) ----------
    st.markdown("#### 1️⃣ ¿Viaja un acompañante?")
    con_acomp = st.checkbox("Sí, somos 2 personas")
    acomp_data = None
    if con_acomp:
        st.caption("Ingresa los datos de tu acompañante (si ya es cliente, lo reconocemos por su documento).")
        ca1, ca2 = st.columns(2)
        a_td = ca1.selectbox("Tipo doc.", ["CC", "CE", "TI", "PAS", "NIT"], key="ac_td")
        a_nd = ca2.text_input("Documento", key="ac_nd")
        a_nom = ca1.text_input("Nombre", key="ac_nom")
        a_ape = ca2.text_input("Apellido", key="ac_ape")
        paises = consultar("SELECT pais_id, nombre FROM av_paises ORDER BY nombre")
        a_pais = ca1.selectbox("País", paises["NOMBRE"].tolist(), key="ac_pais")
        a_fn = ca2.date_input("Fecha nac.", value=date(2000, 1, 1),
                              min_value=date(1920, 1, 1),
                              max_value=date.today() - timedelta(days=1), key="ac_fn")
        acomp_data = {"td": a_td, "nd": a_nd, "nom": a_nom, "ape": a_ape,
                      "pais": a_pais, "fn": a_fn, "paises": paises}

    # ---------- Fechas ----------
    st.markdown("#### 2️⃣ Fechas del viaje")
    cf1, cf2 = st.columns(2)
    fecha_ini = cf1.date_input("Inicio", value=date.today() + timedelta(days=1),
                               min_value=date.today() + timedelta(days=1))
    fecha_fin = cf2.date_input("Fin", value=date.today() + timedelta(days=5),
                               min_value=date.today() + timedelta(days=2))

    st.divider()

    # ---------- Itinerario ----------
    st.markdown("#### 3️⃣ Arma tu itinerario")
    tv, th, tt = st.tabs(["✈️ Vuelos", "🏨 Hospedaje", "🚌 Transporte"])

    with tv:
        vdf = consultar("""
            SELECT v.vuelo_id,
                   al.nombre || ' ' || v.num_vuelo || ' | ' ||
                   ao.codigo_iata || '→' || ad.codigo_iata || ' | ' ||
                   TO_CHAR(v.fecha_salida,'DD/MM/YYYY HH24:MI') AS etiqueta, v.precio_base
            FROM av_vuelos v
            JOIN av_aerolineas al ON v.aerolinea_id = al.aerolinea_id
            JOIN av_aeropuertos ao ON v.aeropuerto_origen_id = ao.aeropuerto_id
            JOIN av_aeropuertos ad ON v.aeropuerto_destino_id = ad.aeropuerto_id
            WHERE v.estado='PROGRAMADO' ORDER BY v.fecha_salida
        """)
        sv = st.selectbox("Vuelo", vdf["ETIQUETA"].tolist(), key="cv")
        if st.button("➕ Agregar vuelo"):
            f = vdf[vdf["ETIQUETA"] == sv].iloc[0]
            st.session_state.rsv_vuelos.append(
                {"id": int(f["VUELO_ID"]), "etiqueta": f["ETIQUETA"], "precio": float(f["PRECIO_BASE"])})
            st.rerun()

    with th:
        hdf = consultar("""
            SELECT hab.habitacion_id,
                   h.nombre || ' | Hab ' || hab.num_habitacion || ' (' || hab.tipo || ') | ' || ci.nombre AS etiqueta,
                   hab.precio_noche
            FROM av_habitaciones hab
            JOIN av_hoteles h ON hab.hotel_id = h.hotel_id
            JOIN av_ciudades ci ON h.ciudad_id = ci.ciudad_id
            WHERE hab.estado='DISPONIBLE' ORDER BY h.nombre
        """)
        sh = st.selectbox("Habitación", hdf["ETIQUETA"].tolist(), key="ch")
        ch1, ch2 = st.columns(2)
        ci = ch1.date_input("Check-in", value=fecha_ini, key="hci")
        co = ch2.date_input("Check-out", value=fecha_fin, key="hco")
        if st.button("➕ Agregar hospedaje"):
            if co <= ci:
                st.warning("El check-out debe ser posterior al check-in.")
            else:
                f = hdf[hdf["ETIQUETA"] == sh].iloc[0]
                noches = (co - ci).days
                st.session_state.rsv_hosp.append(
                    {"id": int(f["HABITACION_ID"]), "etiqueta": f["ETIQUETA"],
                     "checkin": ci, "checkout": co, "noches": noches,
                     "precio_total": noches * float(f["PRECIO_NOCHE"])})
                st.rerun()

    with tt:
        tdf = consultar("""
            SELECT t.transporte_id,
                   t.tipo || ' ' || t.empresa || ' | ' || co.nombre || '→' || cd.nombre || ' | ' ||
                   TO_CHAR(t.fecha_salida,'DD/MM/YYYY') AS etiqueta, t.precio
            FROM av_transportes_terrestres t
            JOIN av_ciudades co ON t.ciudad_origen_id = co.ciudad_id
            JOIN av_ciudades cd ON t.ciudad_destino_id = cd.ciudad_id
            WHERE t.estado='PROGRAMADO' ORDER BY t.fecha_salida
        """)
        stt = st.selectbox("Transporte", tdf["ETIQUETA"].tolist(), key="ct")
        if st.button("➕ Agregar transporte"):
            f = tdf[tdf["ETIQUETA"] == stt].iloc[0]
            st.session_state.rsv_transp.append(
                {"id": int(f["TRANSPORTE_ID"]), "etiqueta": f["ETIQUETA"], "precio": float(f["PRECIO"])})
            st.rerun()

    st.divider()

    # ---------- Resumen ----------
    st.markdown("#### 4️⃣ Resumen")
    total = 0.0
    for v in st.session_state.rsv_vuelos:
        st.write(f"✈️ {v['etiqueta']} — ${v['precio']:,.0f}"); total += v["precio"]
    for h in st.session_state.rsv_hosp:
        st.write(f"🏨 {h['etiqueta']} — {h['noches']} noches — ${h['precio_total']:,.0f}")
        total += h["precio_total"]
    for t in st.session_state.rsv_transp:
        st.write(f"🚌 {t['etiqueta']} — ${t['precio']:,.0f}"); total += t["precio"]

    if total == 0:
        st.info("Agrega al menos un servicio.")
    else:
        st.success(f"💰 Total: **${total:,.0f}**")

    cb1, cb2 = st.columns(2)
    with cb1:
        if st.button("✅ Confirmar reserva", type="primary"):
            if fecha_fin <= fecha_ini:
                st.warning("La fecha de fin debe ser posterior a la de inicio.")
            elif total == 0:
                st.warning("Agrega al menos un servicio.")
            else:
                try:
                    pasajeros = [CID]
                    # Resolver/crear acompañante si aplica
                    if con_acomp and acomp_data:
                        if not (acomp_data["nd"] and acomp_data["nom"] and acomp_data["ape"]):
                            st.warning("Faltan datos del acompañante."); st.stop()
                        pid = int(acomp_data["paises"]
                                  [acomp_data["paises"]["NOMBRE"] == acomp_data["pais"]]["PAIS_ID"].values[0])
                        aid, _ = obtener_o_crear_cliente(
                            acomp_data["td"], acomp_data["nd"], acomp_data["nom"],
                            acomp_data["ape"], acomp_data["fn"], pid)
                        if aid == CID:
                            st.warning("El acompañante no puede ser el mismo titular."); st.stop()
                        pasajeros.append(aid)

                    rid, monto = registrar_reserva_completa(
                        CID, pasajeros, fecha_ini, fecha_fin,
                        st.session_state.rsv_vuelos, st.session_state.rsv_hosp,
                        st.session_state.rsv_transp)
                    st.session_state.rsv_vuelos = []
                    st.session_state.rsv_hosp = []
                    st.session_state.rsv_transp = []
                    st.success(f"¡Reserva #{rid} confirmada por ${monto:,.0f}! 🎉")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error al reservar: {e}")
    with cb2:
        if st.button("🗑️ Vaciar itinerario"):
            st.session_state.rsv_vuelos = []
            st.session_state.rsv_hosp = []
            st.session_state.rsv_transp = []
            st.rerun()


# =====================================================================
#  8. MIS RESERVAS (solo las del cliente logueado)
# =====================================================================

elif pagina == "🔍 Mis reservas":
    st.subheader("🔍 Mis reservas")
    mis = consultar("""
        SELECT r.reserva_id AS "ID",
               TO_CHAR(r.fecha_inicio_viaje,'DD/MM/YYYY') AS "Inicio",
               TO_CHAR(r.fecha_fin_viaje,'DD/MM/YYYY') AS "Fin",
               r.monto_total AS "Monto", r.estado AS "Estado"
        FROM av_reservas r
        WHERE r.cliente_id = :c
        ORDER BY r.reserva_id DESC
    """, {"c": CID})

    if mis.empty:
        st.info("Aún no tienes reservas. Crea una en 📝 Nueva reserva.")
    else:
        st.dataframe(mis, use_container_width=True, hide_index=True)
        st.divider()
        rid = int(st.selectbox("Ver detalle", mis["ID"].tolist()))

        ca, cb = st.columns(2)
        with ca:
            st.write("**✈️ Vuelos**")
            st.dataframe(consultar("""
                SELECT al.nombre || ' ' || v.num_vuelo AS "Vuelo",
                       ao.codigo_iata || '→' || ad.codigo_iata AS "Ruta", rv.precio_aplicado AS "Precio"
                FROM av_reserva_vuelos rv
                JOIN av_vuelos v ON rv.vuelo_id = v.vuelo_id
                JOIN av_aerolineas al ON v.aerolinea_id = al.aerolinea_id
                JOIN av_aeropuertos ao ON v.aeropuerto_origen_id = ao.aeropuerto_id
                JOIN av_aeropuertos ad ON v.aeropuerto_destino_id = ad.aeropuerto_id
                WHERE rv.reserva_id = :r
            """, {"r": rid}), use_container_width=True, hide_index=True)
            st.write("**🚌 Transportes**")
            st.dataframe(consultar("""
                SELECT t.tipo || ' ' || t.empresa AS "Transporte",
                       co.nombre || '→' || cd.nombre AS "Ruta", rt.precio_aplicado AS "Precio"
                FROM av_reserva_transportes rt
                JOIN av_transportes_terrestres t ON rt.transporte_id = t.transporte_id
                JOIN av_ciudades co ON t.ciudad_origen_id = co.ciudad_id
                JOIN av_ciudades cd ON t.ciudad_destino_id = cd.ciudad_id
                WHERE rt.reserva_id = :r
            """, {"r": rid}), use_container_width=True, hide_index=True)
        with cb:
            st.write("**🏨 Hospedajes**")
            st.dataframe(consultar("""
                SELECT h.nombre AS "Hotel", hab.num_habitacion AS "Hab",
                       rh.num_noches AS "Noches", rh.precio_total AS "Precio"
                FROM av_reserva_hospedajes rh
                JOIN av_habitaciones hab ON rh.habitacion_id = hab.habitacion_id
                JOIN av_hoteles h ON hab.hotel_id = h.hotel_id
                WHERE rh.reserva_id = :r
            """, {"r": rid}), use_container_width=True, hide_index=True)
            st.write("**💳 Pagos**")
            st.dataframe(consultar("""
                SELECT TO_CHAR(fecha_pago,'DD/MM/YYYY') AS "Fecha",
                       monto_pago AS "Monto", canal_pago AS "Canal"
                FROM av_pagos WHERE reserva_id = :r ORDER BY fecha_pago
            """, {"r": rid}), use_container_width=True, hide_index=True)


# =====================================================================
#  9. PAGAR (solo reservas del cliente logueado)
# =====================================================================

elif pagina == "💳 Pagar":
    st.subheader("💳 Pagar mis reservas")
    saldos = consultar("""
        SELECT r.reserva_id, r.monto_total,
               r.monto_total - NVL(SUM(p.monto_pago), 0) AS saldo
        FROM av_reservas r
        LEFT JOIN av_pagos p ON r.reserva_id = p.reserva_id
        WHERE r.cliente_id = :c AND r.estado IN ('ACTIVA', 'CONFIRMADA')
        GROUP BY r.reserva_id, r.monto_total
        HAVING r.monto_total - NVL(SUM(p.monto_pago), 0) > 0
        ORDER BY r.reserva_id
    """, {"c": CID})

    if saldos.empty:
        st.info("No tienes saldos pendientes. ✅")
    else:
        etq = ("Reserva " + saldos["RESERVA_ID"].astype(str)
               + " — Saldo $" + saldos["SALDO"].map(lambda x: f"{x:,.0f}"))
        sel = st.selectbox("Reserva", etq.tolist())
        fila = saldos[etq == sel].iloc[0]
        rid = int(fila["RESERVA_ID"])
        saldo = float(fila["SALDO"])
        st.write(f"Saldo pendiente: **${saldo:,.0f}**")

        cp1, cp2 = st.columns(2)
        monto = cp1.number_input("Monto ($)", min_value=0.0, max_value=saldo, value=saldo, step=50000.0)
        fecha_pago = cp1.date_input("Fecha", value=date.today())
        canal = cp2.selectbox("Canal", ["TARJETA DE CREDITO", "TARJETA DEBITO",
                                        "PSE", "TRANSFERENCIA", "EFECTIVO"])
        referencia = cp2.text_input("Referencia")

        if st.button("Pagar", type="primary"):
            if monto <= 0:
                st.warning("El monto debe ser mayor que cero.")
            else:
                try:
                    ejecutar_dml("""INSERT INTO av_pagos
                        (reserva_id, fecha_pago, monto_pago, canal_pago, referencia)
                        VALUES (:r, :f, :m, :c, :ref)""",
                        {"r": rid, "f": fecha_pago, "m": monto, "c": canal, "ref": referencia or None})
                    st.success(f"Pago de ${monto:,.0f} registrado. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error al pagar: {e}")