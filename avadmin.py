# =====================================================================
#  ANDARIEGO  ✈️  — PANEL ADMINISTRATIVO (Agencia)
#  - Catálogos (geografía, hoteles, vuelos, transporte): VER + AGREGAR
#  - Clientes / Reservas / Pagos: VER + ELIMINAR (NO agregar)
# =====================================================================

import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
import oracledb

# =====================================================================
#  1. CONEXIÓN A LA BASE DE DATOS
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
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or {})
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# Elimina una reserva y TODOS sus registros hijos en una transacción.
def eliminar_reserva(rid):
    conn = conectar()
    cur = conn.cursor()
    try:
        for tabla in ["av_notas_cancelacion", "av_pagos", "av_reserva_vuelos",
                      "av_reserva_hospedajes", "av_reserva_transportes",
                      "av_reserva_pasajeros"]:
            cur.execute(f"DELETE FROM {tabla} WHERE reserva_id = :r", {"r": rid})
        cur.execute("DELETE FROM av_reservas WHERE reserva_id = :r", {"r": rid})
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# =====================================================================
#  2. CONFIGURACIÓN Y ESTILOS
# =====================================================================

st.set_page_config(page_title="Andariego · Admin", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F4F8FB; }
    .hero {
        background: linear-gradient(120deg, #0B3D52 0%, #0B6E99 100%);
        padding: 26px 34px; border-radius: 18px; color: white; margin-bottom: 18px;
        box-shadow: 0 6px 24px rgba(11,61,82,0.25);
    }
    .hero h1 { color: white; margin: 0; font-size: 30px; }
    .hero p  { color: #D6EAF2; margin: 6px 0 0 0; font-size: 15px; }
    .kpi {
        background: white; border-radius: 14px; padding: 18px 20px;
        border-left: 5px solid #0B6E99; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .kpi .label { color: #6B7B8C; font-size: 13px; text-transform: uppercase; letter-spacing:.5px; }
    .kpi .value { color: #0B3D52; font-size: 26px; font-weight: 700; margin-top: 4px; }
    .stButton > button[kind="primary"] { background:#0B6E99; border:none; border-radius:10px; font-weight:600; }
    .stButton > button[kind="primary"]:hover { background:#095c80; }
    section[data-testid="stSidebar"] { background-color:#0B3D52; }
    section[data-testid="stSidebar"] * { color:#E8F6FA !important; }
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div>'
                f'<div class="value">{value}</div></div>', unsafe_allow_html=True)


# =====================================================================
#  3. MENÚ
# =====================================================================

st.sidebar.markdown("## 🛠️ Andariego Admin")
st.sidebar.caption("Panel de la agencia")
st.sidebar.divider()

pagina = st.sidebar.radio("Menú", [
    "🏠 Inicio",
    "🌐 Geografía",
    "🏨 Hoteles y habitaciones",
    "✈️ Vuelos",
    "🚌 Transporte terrestre",
    "👤 Clientes",
    "🔍 Reservas",
    "💳 Pagos",
])


# =====================================================================
#  4. INICIO (DASHBOARD)
# =====================================================================

if pagina == "🏠 Inicio":
    st.markdown("""
        <div class="hero"><h1>Panel administrativo 🛠️</h1>
        <p>Gestión de catálogos y supervisión de la operación</p></div>
    """, unsafe_allow_html=True)

    k = consultar("""
        SELECT (SELECT COUNT(*) FROM av_paises) AS paises,
               (SELECT COUNT(*) FROM av_hoteles) AS hoteles,
               (SELECT COUNT(*) FROM av_vuelos) AS vuelos,
               (SELECT COUNT(*) FROM av_clientes) AS clientes,
               (SELECT COUNT(*) FROM av_reservas) AS reservas,
               (SELECT COUNT(*) FROM av_reservas WHERE estado='ACTIVA') AS activas,
               (SELECT NVL(SUM(monto_pago),0) FROM av_pagos) AS ingresos
        FROM dual
    """).iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Países", int(k["PAISES"]))
    with c2: kpi_card("Hoteles", int(k["HOTELES"]))
    with c3: kpi_card("Vuelos", int(k["VUELOS"]))
    with c4: kpi_card("Clientes", int(k["CLIENTES"]))
    st.write("")
    c5, c6, c7 = st.columns(3)
    with c5: kpi_card("Reservas totales", int(k["RESERVAS"]))
    with c6: kpi_card("Reservas activas", int(k["ACTIVAS"]))
    with c7: kpi_card("Ingresos recaudados", f"${k['INGRESOS']:,.0f}")


# =====================================================================
#  5. GEOGRAFÍA (países, ciudades, aeropuertos, aerolíneas) — VER + AGREGAR
# =====================================================================

elif pagina == "🌐 Geografía":
    st.subheader("🌐 Catálogo geográfico")
    tp, tc, ta, tal = st.tabs(["🌎 Países", "🏙️ Ciudades", "🛫 Aeropuertos", "✈️ Aerolíneas"])

    # ----- Países -----
    with tp:
        st.dataframe(consultar("""
            SELECT codigo_iso AS "ISO", nombre AS "País",
                   continente AS "Continente", estado AS "Estado"
            FROM av_paises ORDER BY nombre
        """), use_container_width=True, hide_index=True)
        st.markdown("**➕ Nuevo país**")
        c1, c2, c3 = st.columns(3)
        iso = c1.text_input("Código ISO (3 letras)", max_chars=3)
        nom = c2.text_input("Nombre del país")
        cont = c3.selectbox("Continente",
                            ["AMERICA", "EUROPA", "ASIA", "AFRICA", "OCEANIA", "ANTARTIDA"])
        if st.button("Agregar país", type="primary"):
            if not (iso and nom):
                st.warning("Código ISO y nombre son obligatorios.")
            else:
                try:
                    ejecutar_dml("""INSERT INTO av_paises (codigo_iso, nombre, continente)
                                    VALUES (:i, :n, :c)""",
                                 {"i": iso.upper(), "n": nom, "c": cont})
                    st.success(f"País {nom} agregado. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ----- Ciudades -----
    with tc:
        st.dataframe(consultar("""
            SELECT ci.nombre AS "Ciudad", p.nombre AS "País", ci.estado AS "Estado"
            FROM av_ciudades ci JOIN av_paises p ON ci.pais_id = p.pais_id
            ORDER BY p.nombre, ci.nombre
        """), use_container_width=True, hide_index=True)
        st.markdown("**➕ Nueva ciudad**")
        paises = consultar("SELECT pais_id, nombre FROM av_paises ORDER BY nombre")
        c1, c2 = st.columns(2)
        pais_sel = c1.selectbox("País", paises["NOMBRE"].tolist(), key="ci_pais")
        nom_ci = c2.text_input("Nombre de la ciudad")
        if st.button("Agregar ciudad", type="primary"):
            if not nom_ci:
                st.warning("El nombre es obligatorio.")
            else:
                pid = int(paises[paises["NOMBRE"] == pais_sel]["PAIS_ID"].values[0])
                try:
                    ejecutar_dml("INSERT INTO av_ciudades (pais_id, nombre) VALUES (:p, :n)",
                                 {"p": pid, "n": nom_ci})
                    st.success(f"Ciudad {nom_ci} agregada. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ----- Aeropuertos -----
    with ta:
        st.dataframe(consultar("""
            SELECT a.codigo_iata AS "IATA", a.nombre AS "Aeropuerto",
                   ci.nombre AS "Ciudad", a.estado AS "Estado"
            FROM av_aeropuertos a JOIN av_ciudades ci ON a.ciudad_id = ci.ciudad_id
            ORDER BY ci.nombre
        """), use_container_width=True, hide_index=True)
        st.markdown("**➕ Nuevo aeropuerto**")
        ciudades = consultar("""SELECT ciudad_id, nombre FROM av_ciudades ORDER BY nombre""")
        c1, c2, c3 = st.columns(3)
        iata_a = c1.text_input("Código IATA (3 letras)", max_chars=3, key="ae_iata")
        nom_a = c2.text_input("Nombre del aeropuerto")
        ciu_a = c3.selectbox("Ciudad", ciudades["NOMBRE"].tolist(), key="ae_ciu")
        if st.button("Agregar aeropuerto", type="primary"):
            if not (iata_a and nom_a):
                st.warning("IATA y nombre son obligatorios.")
            else:
                cid = int(ciudades[ciudades["NOMBRE"] == ciu_a]["CIUDAD_ID"].values[0])
                try:
                    ejecutar_dml("""INSERT INTO av_aeropuertos (codigo_iata, nombre, ciudad_id)
                                    VALUES (:i, :n, :c)""",
                                 {"i": iata_a.upper(), "n": nom_a, "c": cid})
                    st.success(f"Aeropuerto {nom_a} agregado. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ----- Aerolíneas -----
    with tal:
        st.dataframe(consultar("""
            SELECT al.codigo_iata AS "IATA", al.nombre AS "Aerolínea",
                   p.nombre AS "País", al.estado AS "Estado"
            FROM av_aerolineas al JOIN av_paises p ON al.pais_id = p.pais_id
            ORDER BY al.nombre
        """), use_container_width=True, hide_index=True)
        st.markdown("**➕ Nueva aerolínea**")
        paises2 = consultar("SELECT pais_id, nombre FROM av_paises ORDER BY nombre")
        c1, c2, c3 = st.columns(3)
        iata_al = c1.text_input("Código IATA (2-3 letras)", max_chars=3, key="al_iata")
        nom_al = c2.text_input("Nombre de la aerolínea")
        pais_al = c3.selectbox("País de origen", paises2["NOMBRE"].tolist(), key="al_pais")
        if st.button("Agregar aerolínea", type="primary"):
            if not (iata_al and nom_al):
                st.warning("IATA y nombre son obligatorios.")
            else:
                pid = int(paises2[paises2["NOMBRE"] == pais_al]["PAIS_ID"].values[0])
                try:
                    ejecutar_dml("""INSERT INTO av_aerolineas (codigo_iata, nombre, pais_id)
                                    VALUES (:i, :n, :p)""",
                                 {"i": iata_al.upper(), "n": nom_al, "p": pid})
                    st.success(f"Aerolínea {nom_al} agregada. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# =====================================================================
#  6. HOTELES Y HABITACIONES — VER + AGREGAR
# =====================================================================

elif pagina == "🏨 Hoteles y habitaciones":
    st.subheader("🏨 Hoteles y habitaciones")
    th, thab = st.tabs(["🏨 Hoteles", "🛏️ Habitaciones"])

    with th:
        st.dataframe(consultar("""
            SELECT h.nombre AS "Hotel", ci.nombre AS "Ciudad",
                   h.estrellas AS "★", h.direccion AS "Dirección", h.estado AS "Estado"
            FROM av_hoteles h JOIN av_ciudades ci ON h.ciudad_id = ci.ciudad_id
            ORDER BY h.nombre
        """), use_container_width=True, hide_index=True)
        st.markdown("**➕ Nuevo hotel**")
        ciudades = consultar("SELECT ciudad_id, nombre FROM av_ciudades ORDER BY nombre")
        c1, c2 = st.columns(2)
        nom_h = c1.text_input("Nombre del hotel")
        ciu_h = c2.selectbox("Ciudad", ciudades["NOMBRE"].tolist(), key="ho_ciu")
        dir_h = c1.text_input("Dirección")
        est_h = c2.slider("Estrellas", 1, 5, 4)
        if st.button("Agregar hotel", type="primary"):
            if not (nom_h and dir_h):
                st.warning("Nombre y dirección son obligatorios.")
            else:
                cid = int(ciudades[ciudades["NOMBRE"] == ciu_h]["CIUDAD_ID"].values[0])
                try:
                    ejecutar_dml("""INSERT INTO av_hoteles (nombre, ciudad_id, direccion, estrellas)
                                    VALUES (:n, :c, :d, :e)""",
                                 {"n": nom_h, "c": cid, "d": dir_h, "e": est_h})
                    st.success(f"Hotel {nom_h} agregado. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with thab:
        st.dataframe(consultar("""
            SELECT h.nombre AS "Hotel", hab.num_habitacion AS "Habitación",
                   hab.tipo AS "Tipo", hab.capacidad AS "Cap.",
                   hab.precio_noche AS "Precio/noche", hab.estado AS "Estado"
            FROM av_habitaciones hab JOIN av_hoteles h ON hab.hotel_id = h.hotel_id
            ORDER BY h.nombre, hab.num_habitacion
        """), use_container_width=True, hide_index=True)
        st.markdown("**➕ Nueva habitación**")
        hoteles = consultar("SELECT hotel_id, nombre FROM av_hoteles ORDER BY nombre")
        c1, c2, c3 = st.columns(3)
        hot_sel = c1.selectbox("Hotel", hoteles["NOMBRE"].tolist(), key="hab_hot")
        num_hab = c2.text_input("N° habitación")
        tipo_hab = c3.selectbox("Tipo", ["SENCILLA", "DOBLE", "SUITE", "FAMILIAR"])
        cap_hab = c1.number_input("Capacidad", 1, 6, 2)
        precio_hab = c2.number_input("Precio por noche ($)", min_value=0.0, value=300000.0, step=50000.0)
        if st.button("Agregar habitación", type="primary"):
            if not num_hab:
                st.warning("El número de habitación es obligatorio.")
            else:
                hid = int(hoteles[hoteles["NOMBRE"] == hot_sel]["HOTEL_ID"].values[0])
                try:
                    ejecutar_dml("""INSERT INTO av_habitaciones
                                    (hotel_id, num_habitacion, tipo, capacidad, precio_noche)
                                    VALUES (:h, :n, :t, :c, :p)""",
                                 {"h": hid, "n": num_hab, "t": tipo_hab,
                                  "c": int(cap_hab), "p": precio_hab})
                    st.success("Habitación agregada. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# =====================================================================
#  7. VUELOS — VER + AGREGAR
# =====================================================================

elif pagina == "✈️ Vuelos":
    st.subheader("✈️ Vuelos")
    st.dataframe(consultar("""
        SELECT v.num_vuelo AS "Vuelo", al.nombre AS "Aerolínea",
               ao.codigo_iata AS "Org", ad.codigo_iata AS "Dst",
               TO_CHAR(v.fecha_salida,'DD/MM/YYYY HH24:MI') AS "Salida",
               v.precio_base AS "Precio", v.asientos_disponibles AS "Asientos",
               v.estado AS "Estado"
        FROM av_vuelos v
        JOIN av_aerolineas al ON v.aerolinea_id = al.aerolinea_id
        JOIN av_aeropuertos ao ON v.aeropuerto_origen_id = ao.aeropuerto_id
        JOIN av_aeropuertos ad ON v.aeropuerto_destino_id = ad.aeropuerto_id
        ORDER BY v.fecha_salida
    """), use_container_width=True, hide_index=True)

    st.markdown("**➕ Nuevo vuelo**")
    aerolineas = consultar("SELECT aerolinea_id, nombre FROM av_aerolineas ORDER BY nombre")
    aeropuertos = consultar("""SELECT aeropuerto_id, codigo_iata || ' - ' || nombre AS etiqueta
                               FROM av_aeropuertos ORDER BY codigo_iata""")
    c1, c2, c3 = st.columns(3)
    al_sel = c1.selectbox("Aerolínea", aerolineas["NOMBRE"].tolist(), key="vu_al")
    num_v = c2.text_input("Número de vuelo")
    precio_v = c3.number_input("Precio base ($)", min_value=0.0, value=500000.0, step=50000.0)
    org_sel = c1.selectbox("Aeropuerto origen", aeropuertos["ETIQUETA"].tolist(), key="vu_org")
    dst_sel = c2.selectbox("Aeropuerto destino", aeropuertos["ETIQUETA"].tolist(), key="vu_dst")
    asientos_v = c3.number_input("Asientos", 0, 500, 120)
    c4, c5, c6, c7 = st.columns(4)
    f_sal = c4.date_input("Fecha salida", value=date.today() + timedelta(days=7), key="vu_fsal")
    h_sal = c5.time_input("Hora salida", value=time(8, 0), key="vu_hsal")
    f_lle = c6.date_input("Fecha llegada", value=date.today() + timedelta(days=7), key="vu_flle")
    h_lle = c7.time_input("Hora llegada", value=time(10, 0), key="vu_hlle")

    if st.button("Agregar vuelo", type="primary"):
        salida = datetime.combine(f_sal, h_sal)
        llegada = datetime.combine(f_lle, h_lle)
        org_id = int(aeropuertos[aeropuertos["ETIQUETA"] == org_sel]["AEROPUERTO_ID"].values[0])
        dst_id = int(aeropuertos[aeropuertos["ETIQUETA"] == dst_sel]["AEROPUERTO_ID"].values[0])
        if not num_v:
            st.warning("El número de vuelo es obligatorio.")
        elif org_id == dst_id:
            st.warning("El origen y el destino no pueden ser iguales.")
        elif llegada <= salida:
            st.warning("La llegada debe ser posterior a la salida.")
        else:
            al_id = int(aerolineas[aerolineas["NOMBRE"] == al_sel]["AEROLINEA_ID"].values[0])
            try:
                ejecutar_dml("""INSERT INTO av_vuelos
                    (aerolinea_id, num_vuelo, aeropuerto_origen_id, aeropuerto_destino_id,
                     fecha_salida, fecha_llegada, precio_base, asientos_disponibles)
                    VALUES (:al, :nv, :org, :dst, :fs, :fl, :pr, :as)""",
                    {"al": al_id, "nv": num_v, "org": org_id, "dst": dst_id,
                     "fs": salida, "fl": llegada, "pr": precio_v, "as": int(asientos_v)})
                st.success(f"Vuelo {num_v} agregado. ✅"); st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


# =====================================================================
#  8. TRANSPORTE TERRESTRE — VER + AGREGAR
# =====================================================================

elif pagina == "🚌 Transporte terrestre":
    st.subheader("🚌 Transporte terrestre")
    st.dataframe(consultar("""
        SELECT t.tipo AS "Tipo", t.empresa AS "Empresa",
               co.nombre AS "Origen", cd.nombre AS "Destino",
               TO_CHAR(t.fecha_salida,'DD/MM/YYYY HH24:MI') AS "Salida",
               t.precio AS "Precio", t.cupos_disponibles AS "Cupos", t.estado AS "Estado"
        FROM av_transportes_terrestres t
        JOIN av_ciudades co ON t.ciudad_origen_id = co.ciudad_id
        JOIN av_ciudades cd ON t.ciudad_destino_id = cd.ciudad_id
        ORDER BY t.fecha_salida
    """), use_container_width=True, hide_index=True)

    st.markdown("**➕ Nuevo transporte**")
    ciudades = consultar("SELECT ciudad_id, nombre FROM av_ciudades ORDER BY nombre")
    c1, c2, c3 = st.columns(3)
    tipo_t = c1.selectbox("Tipo", ["BUS", "TREN", "VAN"])
    empresa_t = c2.text_input("Empresa")
    precio_t = c3.number_input("Precio ($)", min_value=0.0, value=200000.0, step=50000.0)
    org_t = c1.selectbox("Ciudad origen", ciudades["NOMBRE"].tolist(), key="tr_org")
    dst_t = c2.selectbox("Ciudad destino", ciudades["NOMBRE"].tolist(), key="tr_dst")
    cupos_t = c3.number_input("Cupos", 0, 300, 40)
    c4, c5, c6, c7 = st.columns(4)
    f_sal = c4.date_input("Fecha salida", value=date.today() + timedelta(days=7), key="tr_fsal")
    h_sal = c5.time_input("Hora salida", value=time(6, 0), key="tr_hsal")
    f_lle = c6.date_input("Fecha llegada", value=date.today() + timedelta(days=7), key="tr_flle")
    h_lle = c7.time_input("Hora llegada", value=time(14, 0), key="tr_hlle")

    if st.button("Agregar transporte", type="primary"):
        salida = datetime.combine(f_sal, h_sal)
        llegada = datetime.combine(f_lle, h_lle)
        org_id = int(ciudades[ciudades["NOMBRE"] == org_t]["CIUDAD_ID"].values[0])
        dst_id = int(ciudades[ciudades["NOMBRE"] == dst_t]["CIUDAD_ID"].values[0])
        if not empresa_t:
            st.warning("La empresa es obligatoria.")
        elif org_id == dst_id:
            st.warning("El origen y el destino no pueden ser iguales.")
        elif llegada <= salida:
            st.warning("La llegada debe ser posterior a la salida.")
        else:
            try:
                ejecutar_dml("""INSERT INTO av_transportes_terrestres
                    (tipo, empresa, ciudad_origen_id, ciudad_destino_id,
                     fecha_salida, fecha_llegada, precio, cupos_disponibles)
                    VALUES (:t, :e, :org, :dst, :fs, :fl, :pr, :cu)""",
                    {"t": tipo_t, "e": empresa_t, "org": org_id, "dst": dst_id,
                     "fs": salida, "fl": llegada, "pr": precio_t, "cu": int(cupos_t)})
                st.success("Transporte agregado. ✅"); st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


# =====================================================================
#  9. CLIENTES — VER + ELIMINAR (NO agregar)
# =====================================================================

elif pagina == "👤 Clientes":
    st.subheader("👤 Clientes registrados")
    clientes = consultar("""
        SELECT c.cliente_id AS "ID", c.tipo_doc AS "Tipo", c.num_doc AS "Documento",
               c.nombre AS "Nombre", c.apellido AS "Apellido",
               c.email AS "Email", p.nombre AS "País", c.estado AS "Estado"
        FROM av_clientes c JOIN av_paises p ON c.pais_id = p.pais_id
        ORDER BY c.nombre, c.apellido
    """)
    st.write(f"Total: **{len(clientes)}**")
    st.dataframe(clientes, use_container_width=True, hide_index=True)

    if not clientes.empty:
        st.divider()
        st.markdown("#### 🗑️ Eliminar cliente")
        etq = (clientes["Tipo"] + " " + clientes["Documento"] + " — "
               + clientes["Nombre"] + " " + clientes["Apellido"])
        sel = st.selectbox("Cliente", etq.tolist())
        cid = int(clientes[etq == sel]["ID"].values[0])

        # Verificar dependencias antes de borrar
        dep = consultar("""
            SELECT (SELECT COUNT(*) FROM av_reservas WHERE cliente_id = :c) AS titular,
                   (SELECT COUNT(*) FROM av_reserva_pasajeros WHERE cliente_id = :c) AS pasajero
            FROM dual
        """, {"c": cid}).iloc[0]

        if int(dep["TITULAR"]) > 0 or int(dep["PASAJERO"]) > 0:
            st.warning("Este cliente tiene reservas asociadas. Elimina primero esas "
                       "reservas en la sección 🔍 Reservas.")
        else:
            if st.button("Eliminar cliente", type="primary"):
                try:
                    ejecutar_dml("DELETE FROM av_clientes WHERE cliente_id = :c", {"c": cid})
                    st.success("Cliente eliminado. ✅"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# =====================================================================
#  10. RESERVAS — VER detalle + ELIMINAR (NO agregar)
# =====================================================================

elif pagina == "🔍 Reservas":
    st.subheader("🔍 Reservas")
    reservas = consultar("""
        SELECT r.reserva_id AS "ID", c.nombre || ' ' || c.apellido AS "Titular",
               TO_CHAR(r.fecha_inicio_viaje,'DD/MM/YYYY') AS "Inicio",
               TO_CHAR(r.fecha_fin_viaje,'DD/MM/YYYY') AS "Fin",
               r.monto_total AS "Monto", r.estado AS "Estado"
        FROM av_reservas r JOIN av_clientes c ON r.cliente_id = c.cliente_id
        ORDER BY r.reserva_id DESC
    """)
    st.write(f"Total: **{len(reservas)}**")
    st.dataframe(reservas, use_container_width=True, hide_index=True)

    if not reservas.empty:
        st.divider()
        rid = int(st.selectbox("Ver / eliminar reserva", reservas["ID"].tolist()))

        st.write("**👥 Pasajeros**")
        st.dataframe(consultar("""
            SELECT rp.num_pasajero AS "N°", c.nombre || ' ' || c.apellido AS "Nombre"
            FROM av_reserva_pasajeros rp JOIN av_clientes c ON rp.cliente_id = c.cliente_id
            WHERE rp.reserva_id = :r ORDER BY rp.num_pasajero
        """, {"r": rid}), use_container_width=True, hide_index=True)

        st.error("⚠️ Eliminar una reserva borra también sus pasajeros, vuelos, "
                 "hospedajes, transportes, pagos y notas asociadas.")
        if st.button("Eliminar reserva", type="primary"):
            try:
                eliminar_reserva(rid)
                st.success(f"Reserva #{rid} eliminada por completo. ✅"); st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


# =====================================================================
#  11. PAGOS — VER + ELIMINAR (NO agregar)
# =====================================================================

elif pagina == "💳 Pagos":
    st.subheader("💳 Pagos registrados")
    pagos = consultar("""
        SELECT p.pago_id AS "ID", p.reserva_id AS "Reserva",
               c.nombre || ' ' || c.apellido AS "Cliente",
               TO_CHAR(p.fecha_pago,'DD/MM/YYYY') AS "Fecha",
               p.monto_pago AS "Monto", p.canal_pago AS "Canal", p.referencia AS "Referencia"
        FROM av_pagos p
        JOIN av_reservas r ON p.reserva_id = r.reserva_id
        JOIN av_clientes c ON r.cliente_id = c.cliente_id
        ORDER BY p.pago_id DESC
    """)
    st.write(f"Total: **{len(pagos)}**")
    st.dataframe(pagos, use_container_width=True, hide_index=True)

    if not pagos.empty:
        st.divider()
        st.markdown("#### 🗑️ Eliminar pago")
        etq = ("Pago " + pagos["ID"].astype(str) + " — Reserva " + pagos["Reserva"].astype(str)
               + " — $" + pagos["Monto"].map(lambda x: f"{x:,.0f}"))
        sel = st.selectbox("Pago", etq.tolist())
        pid = int(pagos[etq == sel]["ID"].values[0])
        if st.button("Eliminar pago", type="primary"):
            try:
                ejecutar_dml("DELETE FROM av_pagos WHERE pago_id = :p", {"p": pid})
                st.success("Pago eliminado. ✅"); st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")