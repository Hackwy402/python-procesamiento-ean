#!/usr/bin/env python3
"""
generar_datos.py — Datos sintéticos del curso
Universidad Ean · Python para Procesamiento, Calidad y Automatización de Datos

Genera un escenario FICTICIO de un fondo de pensiones con errores de calidad
sembrados a propósito (para practicar limpieza, validación y automatización):

  datos/afiliados.csv            ~3.100 filas  (duplicados, formatos mixtos, nulos…)
  datos/oficinas.xlsx            catálogo de ciudades / regionales (2 hojas)
  datos/aportes/aportes_2026-MM.csv   un archivo por mes (ene–sep 2026)
  datos/pqrs.csv                 ~1.500 solicitudes (peticiones, quejas, reclamos)

TODO es inventado: nombres, documentos, correos y teléfonos NO corresponden a
personas reales. Semilla fija → siempre genera los mismos datos.

Uso:  python generar_datos.py
"""
import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

SEED = 2026
SMMLV = 1_750_905          # Salario mínimo 2026 (verificar valor vigente)
TASA_APORTE = 0.16         # Cotización a pensión: 16 % del IBC

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos")
rng = np.random.default_rng(SEED)
random.seed(SEED)

NOMBRES_F = ["María", "Luisa", "Ana", "Carolina", "Diana", "Paola", "Sandra", "Laura",
             "Natalia", "Claudia", "Andrea", "Juliana", "Valentina", "Gloria", "Marta",
             "Patricia", "Liliana", "Ángela", "Daniela", "Camila", "Yolanda", "Beatriz"]
NOMBRES_M = ["Juan", "Carlos", "Andrés", "Luis", "Jorge", "Diego", "Felipe", "Óscar",
             "Mauricio", "Javier", "Ricardo", "Fernando", "Alejandro", "Sebastián",
             "Camilo", "Héctor", "Hernán", "Julián", "Gustavo", "Álvaro", "Edwin", "Iván"]
APELLIDOS = ["Rodríguez", "Gómez", "González", "Martínez", "García", "López", "Hernández",
             "Sánchez", "Ramírez", "Pérez", "Díaz", "Moreno", "Muñoz", "Rojas", "Vargas",
             "Castro", "Ortiz", "Rubio", "Suárez", "Jiménez", "Torres", "Cárdenas",
             "Quintero", "Ospina", "Restrepo", "Zapata", "Mejía", "Bermúdez", "Peña", "Ríos"]

# ciudad canónica, departamento, código DANE, regional, peso
CIUDADES = [
    ("Bogotá D.C.", "Bogotá D.C.", "11001", "Centro", 30),
    ("Medellín", "Antioquia", "05001", "Antioquia", 13),
    ("Cali", "Valle del Cauca", "76001", "Occidente", 10),
    ("Barranquilla", "Atlántico", "08001", "Caribe", 8),
    ("Cartagena", "Bolívar", "13001", "Caribe", 5),
    ("Bucaramanga", "Santander", "68001", "Oriente", 5),
    ("Pereira", "Risaralda", "66001", "Eje Cafetero", 4),
    ("Manizales", "Caldas", "17001", "Eje Cafetero", 3),
    ("Ibagué", "Tolima", "73001", "Centro", 3),
    ("Cúcuta", "Norte de Santander", "54001", "Oriente", 4),
    ("Villavicencio", "Meta", "50001", "Centro", 3),
    ("Pasto", "Nariño", "52001", "Occidente", 3),
    ("Neiva", "Huila", "41001", "Centro", 3),
    ("Santa Marta", "Magdalena", "47001", "Caribe", 3),
    ("Tunja", "Boyacá", "15001", "Centro", 3),
]
# variantes "sucias" de cómo la gente escribe la ciudad
VARIANTES = {
    "Bogotá D.C.": ["Bogota", "BOGOTÁ D.C.", "bogotá ", "Bogotá", "BOGOTA DC", "Bogota D.C"],
    "Medellín": ["Medellin", "MEDELLÍN", " medellin", "MEDELLIN"],
    "Cali": ["CALI", "cali", "Santiago de Cali"],
    "Barranquilla": ["BARRANQUILLA", "B/quilla", "barranquilla "],
    "Cartagena": ["CARTAGENA", "Cartagena de Indias"],
    "Bucaramanga": ["BUCARAMANGA", "B/manga"],
    "Cúcuta": ["Cucuta", "CÚCUTA"],
    "Ibagué": ["Ibague", "IBAGUE"],
}
OPERADORES = ["Aportes en Línea", "SOI", "Mi Planilla", "Asopagos", "Enlace Operativo"]


def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=int(rng.integers(0, (end - start).days + 1)))


def ensuciar_texto(s: str) -> str:
    r = rng.random()
    if r < 0.4:
        return s.upper()
    if r < 0.7:
        return s.lower()
    return "  " + s + " "


# ---------------------------------------------------------------- afiliados
def generar_afiliados(n=3000) -> pd.DataFrame:
    pesos = np.array([c[4] for c in CIUDADES], dtype=float)
    pesos /= pesos.sum()
    filas, usados = [], set()
    hoy = date(2026, 10, 31)
    for i in range(n):
        genero = "F" if rng.random() < 0.52 else "M"
        nombre = random.choice(NOMBRES_F if genero == "F" else NOMBRES_M)
        if rng.random() < 0.35:
            nombre += " " + random.choice(NOMBRES_F if genero == "F" else NOMBRES_M)
        apellidos = random.choice(APELLIDOS) + " " + random.choice(APELLIDOS)

        while True:
            doc = int(rng.integers(10_000_000, 1_150_000_000))
            if doc not in usados:
                usados.add(doc)
                break
        nac = rand_date(date(1956, 1, 1), date(2005, 12, 31))
        edad = (hoy - nac).days // 365
        inicio_af = max(date(nac.year + 18, nac.month, min(nac.day, 28)), date(1994, 4, 1))
        afil = rand_date(inicio_af, date(2026, 9, 30)) if inicio_af < date(2026, 9, 30) else date(2026, 9, 30)

        edad_pension = 57 if genero == "F" else 62
        if edad >= edad_pension and rng.random() < 0.75:
            estado = "Pensionado"
        else:
            estado = "Activo" if rng.random() < 0.78 else "Inactivo"

        salario = max(SMMLV, round(float(rng.lognormal(np.log(3_000_000), 0.55)), -3))
        c = CIUDADES[rng.choice(len(CIUDADES), p=pesos)]
        user = (nombre.split()[0] + "." + apellidos.split()[0]).lower()
        user = (user.replace("á", "a").replace("é", "e").replace("í", "i")
                    .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
        filas.append({
            "id_afiliado": f"AF{100000 + i}",
            "tipo_documento": "CC" if rng.random() < 0.97 else "CE",
            "numero_documento": str(doc),
            "nombres": nombre,
            "apellidos": apellidos,
            "fecha_nacimiento": nac.isoformat(),
            "genero": genero,
            "ciudad": c[0],
            "departamento": c[1],
            "fecha_afiliacion": afil.isoformat(),
            "salario_base": salario,
            "email": f"{user}{int(rng.integers(1, 999))}@correo.com",
            "telefono": "3" + "".join(str(int(d)) for d in rng.integers(0, 10, 9)),
            "estado": estado,
        })
    df = pd.DataFrame(filas)
    df["salario_base"] = df["salario_base"].astype(object)

    def idx(frac):
        return rng.choice(df.index, size=max(1, int(len(df) * frac)), replace=False)

    # --- errores sembrados -------------------------------------------------
    for i in idx(0.04):  # documento con puntos
        d = df.at[i, "numero_documento"]
        df.at[i, "numero_documento"] = f"{int(d):,}".replace(",", ".")
    for i in idx(0.01):
        df.at[i, "numero_documento"] = " " + df.at[i, "numero_documento"] + " "
    for i in idx(0.005):
        df.at[i, "numero_documento"] = None
    for i in idx(0.08):
        df.at[i, "nombres"] = ensuciar_texto(df.at[i, "nombres"])
    for i in idx(0.05):
        df.at[i, "apellidos"] = ensuciar_texto(df.at[i, "apellidos"])
    for i in idx(0.07):  # fecha en formato dd/mm/aaaa
        d = date.fromisoformat(df.at[i, "fecha_nacimiento"])
        df.at[i, "fecha_nacimiento"] = d.strftime("%d/%m/%Y")
    for i in idx(0.004):  # fechas imposibles
        df.at[i, "fecha_nacimiento"] = random.choice(["2031-05-14", "1890-01-01", "1900-01-01"])
    mapa_gen = {"F": ["f", "Femenino", "FEMENINO", "F "], "M": ["m", "Masculino", "MASCULINO", "M "]}
    for i in idx(0.06):
        df.at[i, "genero"] = random.choice(mapa_gen[df.at[i, "genero"]])
    for i in idx(0.02):
        df.at[i, "genero"] = None
    for i in idx(0.12):
        c = df.at[i, "ciudad"]
        if c in VARIANTES:
            df.at[i, "ciudad"] = random.choice(VARIANTES[c])
    for i in idx(0.01):  # departamento inconsistente con la ciudad
        df.at[i, "departamento"] = random.choice([c[1] for c in CIUDADES if c[1] != df.at[i, "departamento"]])
    for i in idx(0.005):  # afiliación antes de nacer
        nac = df.at[i, "fecha_nacimiento"]
        try:
            d = date.fromisoformat(nac)
            df.at[i, "fecha_afiliacion"] = (d - timedelta(days=int(rng.integers(100, 2000)))).isoformat()
        except ValueError:
            pass
    for i in idx(0.02):
        df.at[i, "salario_base"] = round(SMMLV * float(rng.uniform(0.3, 0.95)), -3)
    for i in idx(0.005):
        df.at[i, "salario_base"] = -abs(df.at[i, "salario_base"])
    for i in idx(0.01):
        df.at[i, "salario_base"] = None
    for i in idx(0.02):  # salario como texto con puntos de miles
        v = df.at[i, "salario_base"]
        if v is not None and v == v:
            df.at[i, "salario_base"] = f"{int(v):,}".replace(",", ".")
    for i in idx(0.03):
        e = df.at[i, "email"]
        df.at[i, "email"] = random.choice([e.replace("@", ""), "sin correo", e.replace(".com", ""),
                                           e.upper(), "N/A", e.replace("@", " @ ")])
    for i in idx(0.03):
        df.at[i, "telefono"] = random.choice([df.at[i, "telefono"][:7], "0000000000",
                                              "601" + df.at[i, "telefono"][3:], None])
    for i in idx(0.02):  # pensionado demasiado joven (incoherencia de negocio)
        if df.at[i, "estado"] == "Activo":
            df.at[i, "estado"] = "Pensionado"
    for i in idx(0.03):
        df.at[i, "estado"] = random.choice(["activo", "ACTIVO", "Activo ", "inactivo", "Pensionada"])

    # duplicados exactos (3 %) y casi duplicados (1 %)
    dup_exact = df.loc[idx(0.03)].copy()
    casi = df.loc[idx(0.01)].copy()
    casi["nombres"] = casi["nombres"].str.upper()
    casi["id_afiliado"] = [f"AF{900000 + k}" for k in range(len(casi))]
    df = pd.concat([df, dup_exact, casi], ignore_index=True)
    df["salario_base"] = df["salario_base"].map(
        lambda v: int(v) if isinstance(v, (int, float)) and v == v else v)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return df


# ---------------------------------------------------------------- oficinas
def generar_oficinas(path):
    ciudades = pd.DataFrame(
        [(c[0], c[1], c[2], c[3]) for c in CIUDADES],
        columns=["ciudad", "departamento", "codigo_dane", "regional"])
    regionales = pd.DataFrame({
        "regional": ["Centro", "Antioquia", "Occidente", "Caribe", "Oriente", "Eje Cafetero"],
        "director": ["Dir. Regional Centro", "Dir. Regional Antioquia", "Dir. Regional Occidente",
                     "Dir. Regional Caribe", "Dir. Regional Oriente", "Dir. Regional Eje Cafetero"],
        "meta_recaudo_mensual": [9.5e9, 4.0e9, 4.2e9, 4.8e9, 2.9e9, 2.1e9],
    })
    with pd.ExcelWriter(path) as xw:
        ciudades.to_excel(xw, sheet_name="ciudades", index=False)
        regionales.to_excel(xw, sheet_name="regionales", index=False)


# ---------------------------------------------------------------- aportes
def generar_aportes(af: pd.DataFrame, carpeta: str):
    os.makedirs(carpeta, exist_ok=True)
    base = af.drop_duplicates("id_afiliado")
    base = base[base["estado"].astype(str).str.strip().str.lower() == "activo"]
    ids = base["id_afiliado"].tolist()
    sal = pd.to_numeric(base["salario_base"], errors="coerce").fillna(SMMLV).abs().clip(lower=SMMLV)
    sal_map = dict(zip(ids, sal))
    for mes in range(1, 10):
        periodo = f"2026-{mes:02d}"
        filas = []
        for aid in ids:
            if rng.random() > 0.92:
                continue
            ibc = sal_map[aid] * (1 + (0.05 if mes >= 2 and rng.random() < 0.1 else 0))
            ibc = int(round(ibc, -3))
            pago = date(2026, mes, 1) + timedelta(days=int(rng.integers(31, 52)))
            if rng.random() < 0.05:
                pago += timedelta(days=int(rng.integers(30, 90)))  # pago tardío
            filas.append([aid, periodo, ibc, round(ibc * TASA_APORTE), pago.isoformat(),
                          random.choice(OPERADORES)])
        df = pd.DataFrame(filas, columns=["id_afiliado", "periodo", "ibc", "valor_aporte",
                                          "fecha_pago", "operador"])
        n = len(df)
        k = lambda f: rng.choice(df.index, size=max(1, int(n * f)), replace=False)
        for i in k(0.01):
            df.at[i, "valor_aporte"] = round(df.at[i, "valor_aporte"] * float(rng.uniform(0.5, 0.9)))
        for i in k(0.005):
            df.at[i, "ibc"] = int(round(SMMLV * float(rng.uniform(0.4, 0.9)), -3))
            df.at[i, "valor_aporte"] = round(df.at[i, "ibc"] * TASA_APORTE)
        huerfanos = df.loc[k(0.005)].copy()
        huerfanos["id_afiliado"] = [f"AF{800000 + int(rng.integers(0, 9999))}" for _ in range(len(huerfanos))]
        df = pd.concat([df, huerfanos, df.loc[k(0.003)]], ignore_index=True)
        ruta = os.path.join(carpeta, f"aportes_{periodo}.csv")
        if mes == 7:
            # julio llegó "distinto": separador ; y encabezados en mayúscula
            df.columns = [c.upper() for c in df.columns]
            df.to_csv(ruta, index=False, sep=";")
        else:
            df.to_csv(ruta, index=False)


# ---------------------------------------------------------------- pqrs
def generar_pqrs(af: pd.DataFrame, n=1500) -> pd.DataFrame:
    ids = af["id_afiliado"].drop_duplicates().tolist()
    tipos = ["Petición", "Queja", "Reclamo", "Sugerencia", "Felicitación"]
    p_tipos = [0.55, 0.15, 0.22, 0.05, 0.03]
    temas = ["Historia laboral", "Pensión de vejez", "Corrección de datos", "Certificados",
             "Devolución de aportes", "Atención al usuario"]
    canales = ["Web", "Presencial", "Telefónico", "Correo electrónico"]
    filas = []
    for i in range(n):
        rad = rand_date(date(2026, 1, 2), date(2026, 10, 30))
        dias = int(rng.gamma(2.2, 6))  # tiempo de respuesta (días calendario)
        resp = rad + timedelta(days=dias)
        estado = "Cerrado"
        if resp > date(2026, 10, 31) or rng.random() < 0.08:
            resp, estado = None, random.choice(["Abierto", "En trámite"])
        filas.append({
            "radicado": f"PQRS-2026-{i + 1:06d}",
            "id_afiliado": random.choice(ids),
            "tipo": rng.choice(tipos, p=p_tipos),
            "tema": random.choice(temas),
            "canal": random.choice(canales),
            "fecha_radicacion": rad.isoformat(),
            "fecha_respuesta": resp.isoformat() if resp else None,
            "estado": estado,
        })
    df = pd.DataFrame(filas)
    for i in rng.choice(df.index, 15, replace=False):  # respuesta antes de radicar
        if df.at[i, "fecha_respuesta"]:
            r = date.fromisoformat(df.at[i, "fecha_radicacion"])
            df.at[i, "fecha_respuesta"] = (r - timedelta(days=int(rng.integers(1, 10)))).isoformat()
    for i in rng.choice(df.index, 30, replace=False):  # cerrado sin fecha de respuesta
        df.at[i, "estado"] = "Cerrado"
        df.at[i, "fecha_respuesta"] = None
    return df


def main():
    os.makedirs(BASE, exist_ok=True)
    af = generar_afiliados()
    af.to_csv(os.path.join(BASE, "afiliados.csv"), index=False, encoding="utf-8")
    generar_oficinas(os.path.join(BASE, "oficinas.xlsx"))
    generar_aportes(af, os.path.join(BASE, "aportes"))
    generar_pqrs(af).to_csv(os.path.join(BASE, "pqrs.csv"), index=False, encoding="utf-8")
    print("Datos generados en", os.path.abspath(BASE))
    for root, _, files in os.walk(BASE):
        for f in sorted(files):
            p = os.path.join(root, f)
            print(f"  {os.path.relpath(p, BASE):35s} {os.path.getsize(p) / 1024:8.1f} KB")


if __name__ == "__main__":
    main()
