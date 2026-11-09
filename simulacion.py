"""
simulacion.py
=============
Lógica de la simulación de eventos discretos del TP 5 – Degustación H
(sin interfaz; la interfaz está en app.py).

Sistema
-------
                      ┌──────────── Portón (2 operarios, 1 cola) ────────────┐
  Autos  U(3;7) ────► │ Cola portón ─► Op1 / Op2  (acreditación Exp(2))     │ ─► Estacionamiento (3 min) ─┐
                      └──────────────────────────────────────────────────────┘                             │
                                                                                                           ▼
                      ┌──────────── Acceso Peatonal ────────────────────────┐                     Sala de degustación
  Peatones 2,5 min ─► │ 50 % QR       : Cola QR    ─► Dispositivo (0,5 min)  │ ──────────────────► (tiempo por Euler:
                      │ 50 % Presenc. : Cola recep.─► Recepcionista U(1;3) │                      dE/dt = -68 - E²/E0)
                      └──────────────────────────────────────────────────────┘                             │
                                                                                                           ▼
                                                                                                         Salida

Reglas de esta implementación
-----------------------------
* UN SOLO generador congruencial mixto, compartido por todas las variables
  aleatorias (X(i) = (a·X(i-1) + c) mod m ; RND = X(i) / m).
* El programa trabaja SOLO con el estado actual (vector actual). No se guarda
  la simulación completa: solo las i filas que se piden mostrar a partir de
  la hora j y la última fila.
* La simulación termina al llegar al tiempo X o a N iteraciones (lo que
  ocurra primero). Si termina por X, la última fila es el evento
  "Fin simulación" con reloj = X.
"""

import math
from collections import deque


# ---------------------------------------------------------------------------
# 1) GENERADOR CONGRUENCIAL MIXTO (uno solo, compartido)
# ---------------------------------------------------------------------------
class GeneradorCongruencialMixto:
    """
        X(i)   = (a · X(i-1) + c) mod m
        RND(i) = X(i) / m          → número en [0 ; 1)

    Todas las variables aleatorias le piden el siguiente número a ESTE mismo
    objeto, en el orden en que se van necesitando.
    """

    def __init__(self, semilla, a, c, m):
        self.x = semilla
        self.a = a
        self.c = c
        self.m = m
        self.usados = 0          # cuántos RND se generaron (dato informativo)

    def siguiente(self):
        self.x = (self.a * self.x + self.c) % self.m
        self.usados += 1
        return self.x / self.m


def periodo_generador(semilla, a, c, m):
    """
    Devuelve (cola, periodo): cuántos números aparecen antes de entrar al
    ciclo y cuántos números distintos tiene el ciclo.
    Con los valores del TP (1234, 1714, 1221, 3922) el período es 468,
    porque mcd(c, m) = 37 ≠ 1 y no se cumple el teorema de Hull-Dobell.
    """
    visto = {}
    x, i = semilla, 0
    while x not in visto and i <= m + 1:
        visto[x] = i
        x = (a * x + c) % m
        i += 1
    return visto.get(x, 0), i - visto.get(x, 0)


# ---------------------------------------------------------------------------
# 2) DISTRIBUCIONES (transformada inversa)
# ---------------------------------------------------------------------------
def uniforme(rnd, a, b):
    """U[a ; b]:  X = a + (b - a) · RND"""
    return a + (b - a) * rnd


def exponencial(rnd, media):
    """Exponencial negativa:  X = -media · ln(1 - RND)   (1-RND nunca es 0)"""
    return -media * math.log(1 - rnd)


# ---------------------------------------------------------------------------
# 3) INTEGRACIÓN NUMÉRICA POR EULER
#    dE/dt = -k - E² / E0        (k = 68 ; 1 unidad de t = 1 minuto)
#    Se integra desde E = E0 hasta que E llega a 0 (el invitado se retira).
# ---------------------------------------------------------------------------
def integrar_euler(E0, h, k):
    """
    Tabla de Euler:
        t(i+1) = t(i) + h
        E(i+1) = E(i) + h · (dE/dt)(i)        con (dE/dt)(i) = -k - E(i)²/E0
    Se corta en la primera fila en que E(i+1) <= 0.
    El tiempo de permanencia es T = t(i+1) de esa fila.
    """
    filas = []
    t, E, i = 0.0, float(E0), 0
    while True:
        derivada = -k - (E * E) / E0
        E_sig = E + h * derivada
        t_sig = round((i + 1) * h, 10)      # i·h evita acumular error de redondeo
        filas.append({"i": i, "t(i)": t, "E(i)": E, "dE/dt": derivada,
                      "t(i+1)": t_sig, "E(i+1)": E_sig})
        i += 1
        t, E = t_sig, E_sig
        if E <= 0 or i > 1_000_000:
            break
    return {"E0": E0, "h": h, "k": k, "T": t, "filas": filas}


def permanencia_exacta(E0, k):
    """
    Solución analítica (solo para comparar con Euler):
        T = (E0 / √(k·E0)) · arctan(E0 / √(k·E0))
    """
    raiz = math.sqrt(k * E0)
    return (E0 / raiz) * math.atan(E0 / raiz)


# ---------------------------------------------------------------------------
# 4) PARÁMETROS POR DEFECTO (valores del enunciado)
# ---------------------------------------------------------------------------
DISTRIBUCIONES_PEATON = ["Constante", "Exponencial negativa", "Uniforme (media ± Δ)"]

PARAMETROS_DEFECTO = {
    # --- Simulación y visualización
    "tiempo_X": 10000.0,        # minutos a simular
    "max_iteraciones": 100000,  # tope de filas del vector de estado
    "mostrar_i": 50,            # cuántas filas mostrar
    "desde_hora_j": 0.0,        # desde qué hora (reloj) mostrar

    # --- Generador congruencial mixto (compartido)
    "semilla": 1234, "a": 1714, "c": 1221, "m": 3922,

    # --- Ingreso vehicular
    "auto_media": 5.0, "auto_delta": 2.0,    # llegadas cada 5 ± 2 min  → U(3;7)
    "porton_media": 2.0,                     # acreditación Exp. negativa media 2
    "estacionamiento": 3.0,                  # constante

    # --- Acceso peatonal
    "peaton_dist": "Constante",              # ver DISTRIBUCIONES_PEATON
    "peaton_media": 2.5,                     # tiempo entre llegadas
    "peaton_delta": 0.5,                     # solo si se elige Uniforme
    "porc_qr": 50.0,                         # % con acreditación digital
    "escaneo_qr": 0.5,                       # 30 segundos (constante)
    "recep_min": 1.0, "recep_max": 3.0,      # recepcionista U(1;3)

    # --- Sala: expectativa y Euler
    "exp_nombres": ["Poca", "Normal", "Mucha"],
    "exp_valores": [1000.0, 1500.0, 2000.0],
    "exp_probs": [1 / 3, 1 / 3, 1 / 3],
    "euler_h": 0.1,
    "euler_k": 68.0,
}

# Códigos de estado de los objetos temporales (para la leyenda)
ESTADOS_IV = {
    "EA": "Esperando acreditación en el portón (en cola)",
    "SA-Op1": "Siendo acreditado por el Operario 1",
    "SA-Op2": "Siendo acreditado por el Operario 2",
    "EST": "Estacionando",
    "ED": "En degustación (en la sala)",
}
ESTADOS_IP = {
    "EQR": "Esperando el dispositivo QR (en cola)",
    "SQR": "Escaneando QR",
    "ER": "Esperando a la recepcionista (en cola)",
    "SR": "Siendo acreditado por la recepcionista",
    "ED": "En degustación (en la sala)",
}

LIBRE, OCUPADO = "Libre", "Ocupado"

# Columnas fijas del vector de estado (los objetos temporales se agregan aparte)
GRUPOS_COLUMNAS = [
    ("Evento", ["Fila", "Evento", "Reloj"]),
    ("Llegada auto", ["RND lleg. auto", "T. entre lleg. auto", "Próx. lleg. auto"]),
    ("Acreditación portón", ["RND acred. portón", "T. acred. portón",
                             "Fin acred. Op1", "Fin acred. Op2"]),
    ("Estacionamiento", ["T. estac.", "Fin estac.", "Próx. fin estac."]),
    ("Llegada peatón", ["RND lleg. peatón", "T. entre lleg. peatón",
                        "Próx. lleg. peatón", "RND tipo acred.", "Tipo acred."]),
    ("Escaneo QR", ["T. escaneo QR", "Fin escaneo QR"]),
    ("Acreditación recepcionista", ["RND acred. recep.", "T. acred. recep.",
                                    "Fin acred. recep."]),
    ("Ingreso a la sala (Euler)", ["RND expectativa", "Expectativa", "E0",
                                   "T. permanencia (Euler)", "Fin degust.",
                                   "Próx. fin degust."]),
    ("Valores del evento", ["Demora AP (este inv.)",
                            "Permanencia (este inv.)"]),
    ("Servidores y colas", ["Op1 estado", "Op2 estado", "Cola portón",
                            "QR estado", "Cola QR", "Recep. estado",
                            "Cola recep.", "Cant. estacionando",
                            "Cant. en sala"]),
    ("Estadísticas", ["AC t libre recep.", "% t libre recep.",
                      "AC t ocupado QR", "% uso QR",
                      "AC demora AP", "Cant. acreditados AP", "Prom. demora AP",
                      "AC espera cola AP", "Cant. inician atención AP",
                      "Prom. espera cola AP",
                      "AC permanencia", "Cant. salidas", "Prom. permanencia"]),
]
COLUMNAS_FIJAS = [c for _, cols in GRUPOS_COLUMNAS for c in cols]

ATRIBUTOS_TEMPORALES = {
    "IV": ["Estado", "Hora llegada", "Fin estac.", "E0", "Fin degust."],
    "IP": ["Estado", "Tipo", "Hora llegada", "E0", "Fin degust."],
}


# ---------------------------------------------------------------------------
# 5) OBJETO TEMPORAL: INVITADO
# ---------------------------------------------------------------------------
class Invitado:
    """
    clase = "IV" (Invitado Vehicular: llega en auto por el portón)
          = "IP" (Invitado Peatonal: llega por el Acceso Peatonal)
    """
    __slots__ = ("clase", "id", "nombre", "estado", "hora_llegada", "tipo",
                 "fin_estac", "E0", "fin_deg")

    def __init__(self, clase, id_, hora_llegada):
        self.clase = clase
        self.id = id_
        self.nombre = f"{clase}{id_}"
        self.estado = None
        self.hora_llegada = hora_llegada
        self.tipo = None          # solo IP: "QR" o "Presencial"
        self.fin_estac = None     # solo IV
        self.E0 = None
        self.fin_deg = None

    def atributos(self):
        if self.clase == "IV":
            return {"Estado": self.estado, "Hora llegada": self.hora_llegada,
                    "Fin estac.": self.fin_estac, "E0": self.E0,
                    "Fin degust.": self.fin_deg}
        return {"Estado": self.estado, "Tipo": self.tipo,
                "Hora llegada": self.hora_llegada, "E0": self.E0,
                "Fin degust.": self.fin_deg}


# ---------------------------------------------------------------------------
# 6) VALIDACIÓN DE PARÁMETROS
# ---------------------------------------------------------------------------
def validar(p):
    errores = []
    if p["m"] <= 0:
        errores.append("El módulo m debe ser mayor que 0.")
    if not (0 <= p["semilla"] < p["m"]):
        errores.append("La semilla debe estar entre 0 y m - 1.")
    if p["tiempo_X"] <= 0:
        errores.append("El tiempo X a simular debe ser mayor que 0.")
    if not (1 <= p["max_iteraciones"] <= 100000):
        errores.append("La cantidad máxima de iteraciones debe estar entre 1 y 100.000.")
    if p["auto_media"] - p["auto_delta"] < 0 or p["auto_delta"] < 0:
        errores.append("Llegada de autos: media - Δ no puede ser negativo.")
    if p["porton_media"] <= 0:
        errores.append("La media de acreditación en el portón debe ser > 0.")
    if p["peaton_media"] <= 0:
        errores.append("El tiempo entre llegadas peatonales debe ser > 0.")
    if p["peaton_dist"].startswith("Uniforme") and (
            p["peaton_delta"] < 0 or p["peaton_media"] - p["peaton_delta"] < 0):
        errores.append("Llegada de peatones uniforme: media - Δ no puede ser negativo.")
    if not (0 <= p["porc_qr"] <= 100):
        errores.append("El % de acreditación digital debe estar entre 0 y 100.")
    if p["recep_max"] < p["recep_min"] or p["recep_min"] < 0:
        errores.append("Recepcionista: el máximo debe ser ≥ al mínimo (y ≥ 0).")
    if abs(sum(p["exp_probs"]) - 1) > 0.001:
        errores.append("Las probabilidades de la expectativa deben sumar 1.")
    if any(v <= 0 for v in p["exp_valores"]):
        errores.append("Los valores de expectativa E0 deben ser > 0.")
    if p["euler_h"] <= 0:
        errores.append("El paso h de Euler debe ser > 0.")
    if p["mostrar_i"] < 1:
        errores.append("Hay que mostrar al menos 1 fila.")
    return errores


# ---------------------------------------------------------------------------
# 7) SIMULACIÓN
# ---------------------------------------------------------------------------
class Simulacion:

    # Prioridad para eventos simultáneos: primero se liberan recursos
    # (salidas y fines de atención) y después entran las llegadas.
    PRIORIDAD = {"FD": 0, "FE": 1, "FAO1": 2, "FAO2": 3, "FQR": 4,
                 "FAR": 5, "LLA": 6, "LLP": 7}

    def __init__(self, p):
        self.p = p
        self.gen = GeneradorCongruencialMixto(p["semilla"], p["a"], p["c"], p["m"])

        # Integraciones de Euler: una por cada valor posible de E0
        self.tablas_euler = {}
        for E0 in p["exp_valores"]:
            if E0 not in self.tablas_euler:
                self.tablas_euler[E0] = integrar_euler(E0, p["euler_h"], p["euler_k"])

        # Tabla de rangos de la expectativa (probabilidad acumulada)
        self.rangos_exp = []
        acum = 0.0
        for nombre, valor, prob in zip(p["exp_nombres"], p["exp_valores"], p["exp_probs"]):
            desde = acum
            acum += prob
            self.rangos_exp.append({"Expectativa": nombre, "E0": valor,
                                    "P()": prob, "RND desde": desde,
                                    "RND hasta (<)": acum})
        self.rangos_exp[-1]["RND hasta (<)"] = 1.0

        # --- Reloj y contador de filas
        self.reloj = 0.0
        self.n = 0

        # --- Próximos eventos "fijos"
        self.prox_lleg_auto = None
        self.fin_acred = [None, None]     # Op1, Op2
        self.prox_lleg_peaton = None
        self.fin_qr = None
        self.fin_rec = None

        # --- Objetos permanentes
        self.op_estado = [LIBRE, LIBRE]
        self.op_atiende = [None, None]
        self.qr_estado, self.qr_atiende = LIBRE, None
        self.rec_estado, self.rec_atiende = LIBRE, None

        # --- Colas (FIFO)
        self.cola_porton = deque()
        self.cola_qr = deque()
        self.cola_rec = deque()

        # --- Objetos temporales vivos
        self.estacionando = []
        self.en_sala = []
        self.vivos = {}
        self.cont_iv = 0
        self.cont_ip = 0

        # --- Acumuladores / contadores
        self.ac_libre_rec = 0.0
        self.ac_ocup_qr = 0.0
        self.ac_demora_ap = 0.0
        self.cant_acred_ap = 0
        self.ac_espera_ap = 0.0
        self.cant_inicio_ap = 0
        self.ac_perm = 0.0
        self.cant_salidas = 0
        self.cant_qr = 0
        self.cant_presencial = 0

    # ----------------------------------------------------------- auxiliares
    def _crear_invitado(self, clase):
        if clase == "IV":
            self.cont_iv += 1
            inv = Invitado("IV", self.cont_iv, self.reloj)
        else:
            self.cont_ip += 1
            inv = Invitado("IP", self.cont_ip, self.reloj)
        self.vivos[inv.nombre] = inv
        return inv

    def _tiempo_entre_llegadas_peaton(self, f):
        p = self.p
        dist = p["peaton_dist"]
        if dist == "Constante":
            t = p["peaton_media"]
        elif dist == "Exponencial negativa":
            rnd = self.gen.siguiente()
            f["RND lleg. peatón"] = rnd
            t = exponencial(rnd, p["peaton_media"])
        else:
            rnd = self.gen.siguiente()
            f["RND lleg. peatón"] = rnd
            t = uniforme(rnd, p["peaton_media"] - p["peaton_delta"],
                         p["peaton_media"] + p["peaton_delta"])
        f["T. entre lleg. peatón"] = t
        self.prox_lleg_peaton = self.reloj + t

    def _generar_llegada_auto(self, f):
        p = self.p
        rnd = self.gen.siguiente()
        t = uniforme(rnd, p["auto_media"] - p["auto_delta"],
                     p["auto_media"] + p["auto_delta"])
        f["RND lleg. auto"] = rnd
        f["T. entre lleg. auto"] = t
        self.prox_lleg_auto = self.reloj + t

    def _iniciar_acred_porton(self, k, inv, f):
        rnd = self.gen.siguiente()
        t = exponencial(rnd, self.p["porton_media"])
        f["RND acred. portón"] = rnd
        f["T. acred. portón"] = t
        self.fin_acred[k] = self.reloj + t
        self.op_estado[k] = OCUPADO
        self.op_atiende[k] = inv
        inv.estado = f"SA-Op{k + 1}"

    def _iniciar_qr(self, inv, f):
        t = self.p["escaneo_qr"]
        f["T. escaneo QR"] = t
        self.fin_qr = self.reloj + t
        self.qr_estado, self.qr_atiende = OCUPADO, inv
        inv.estado = "SQR"
        self.ac_espera_ap += self.reloj - inv.hora_llegada
        self.cant_inicio_ap += 1

    def _iniciar_rec(self, inv, f):
        rnd = self.gen.siguiente()
        t = uniforme(rnd, self.p["recep_min"], self.p["recep_max"])
        f["RND acred. recep."] = rnd
        f["T. acred. recep."] = t
        self.fin_rec = self.reloj + t
        self.rec_estado, self.rec_atiende = OCUPADO, inv
        inv.estado = "SR"
        self.ac_espera_ap += self.reloj - inv.hora_llegada
        self.cant_inicio_ap += 1

    def _expectativa(self, rnd):
        for r in self.rangos_exp:
            if rnd < r["RND hasta (<)"]:
                return r["Expectativa"], r["E0"]
        return self.rangos_exp[-1]["Expectativa"], self.rangos_exp[-1]["E0"]

    def _ingresar_sala(self, inv, f):
        rnd = self.gen.siguiente()
        nombre, E0 = self._expectativa(rnd)
        T = self.tablas_euler[E0]["T"]
        inv.estado = "ED"
        inv.E0 = E0
        inv.fin_deg = self.reloj + T
        self.en_sala.append(inv)
        f["RND expectativa"] = rnd
        f["Expectativa"] = nombre
        f["E0"] = E0
        f["T. permanencia (Euler)"] = T
        f["Fin degust."] = inv.fin_deg

    def _fin_acreditacion_ap(self, inv, f):
        """El invitado peatonal termina de acreditarse: pasa a la sala."""
        demora = self.reloj - inv.hora_llegada
        self.ac_demora_ap += demora
        self.cant_acred_ap += 1
        f["Demora AP (este inv.)"] = demora
        self._ingresar_sala(inv, f)

    # ----------------------------------------------------------- eventos
    def _inicializar(self):
        f = {"Evento": "Inicialización"}
        self._generar_llegada_auto(f)
        self._tiempo_entre_llegadas_peaton(f)
        return f

    def _llegada_auto(self, f):
        self._generar_llegada_auto(f)
        inv = self._crear_invitado("IV")
        f["Evento"] = f"Llegada auto ({inv.nombre})"
        if self.op_estado[0] == LIBRE:
            self._iniciar_acred_porton(0, inv, f)
        elif self.op_estado[1] == LIBRE:
            self._iniciar_acred_porton(1, inv, f)
        else:
            inv.estado = "EA"
            self.cola_porton.append(inv)

    def _fin_acred_porton(self, k, f):
        inv = self.op_atiende[k]
        f["Evento"] = f"Fin acred. portón Op{k + 1} ({inv.nombre})"
        inv.estado = "EST"
        inv.fin_estac = self.reloj + self.p["estacionamiento"]
        self.estacionando.append(inv)
        f["T. estac."] = self.p["estacionamiento"]
        f["Fin estac."] = inv.fin_estac
        if self.cola_porton:
            self._iniciar_acred_porton(k, self.cola_porton.popleft(), f)
        else:
            self.op_estado[k] = LIBRE
            self.op_atiende[k] = None
            self.fin_acred[k] = None

    def _fin_estacionamiento(self, inv, f):
        f["Evento"] = f"Fin estacionamiento ({inv.nombre})"
        self.estacionando.remove(inv)
        inv.fin_estac = None
        self._ingresar_sala(inv, f)

    def _llegada_peaton(self, f):
        p = self.p
        self._tiempo_entre_llegadas_peaton(f)
        inv = self._crear_invitado("IP")
        f["Evento"] = f"Llegada peatón ({inv.nombre})"
        rnd = self.gen.siguiente()
        inv.tipo = "QR" if rnd < p["porc_qr"] / 100 else "Presencial"
        f["RND tipo acred."] = rnd
        f["Tipo acred."] = inv.tipo
        if inv.tipo == "QR":
            self.cant_qr += 1
            if self.qr_estado == LIBRE:
                self._iniciar_qr(inv, f)
            else:
                inv.estado = "EQR"
                self.cola_qr.append(inv)
        else:
            self.cant_presencial += 1
            if self.rec_estado == LIBRE:
                self._iniciar_rec(inv, f)
            else:
                inv.estado = "ER"
                self.cola_rec.append(inv)

    def _fin_escaneo_qr(self, f):
        inv = self.qr_atiende
        f["Evento"] = f"Fin escaneo QR ({inv.nombre})"
        self._fin_acreditacion_ap(inv, f)
        if self.cola_qr:
            self._iniciar_qr(self.cola_qr.popleft(), f)
        else:
            self.qr_estado, self.qr_atiende, self.fin_qr = LIBRE, None, None

    def _fin_acred_recep(self, f):
        inv = self.rec_atiende
        f["Evento"] = f"Fin acred. recep. ({inv.nombre})"
        self._fin_acreditacion_ap(inv, f)
        if self.cola_rec:
            self._iniciar_rec(self.cola_rec.popleft(), f)
        else:
            self.rec_estado, self.rec_atiende, self.fin_rec = LIBRE, None, None

    def _fin_degustacion(self, inv, f):
        f["Evento"] = f"Fin degustación ({inv.nombre})"
        self.en_sala.remove(inv)
        del self.vivos[inv.nombre]          # el objeto temporal deja de existir
        perm = self.reloj - inv.hora_llegada
        self.ac_perm += perm
        self.cant_salidas += 1
        f["Permanencia (este inv.)"] = perm

    # ----------------------------------------------------------- motor
    def _proximo_evento(self):
        """Devuelve (hora, prioridad, código, objeto) del evento más próximo."""
        cands = [(self.prox_lleg_auto, self.PRIORIDAD["LLA"], "LLA", None),
                 (self.prox_lleg_peaton, self.PRIORIDAD["LLP"], "LLP", None)]
        if self.en_sala:
            inv = min(self.en_sala, key=lambda x: x.fin_deg)
            cands.append((inv.fin_deg, self.PRIORIDAD["FD"], "FD", inv))
        if self.estacionando:
            inv = min(self.estacionando, key=lambda x: x.fin_estac)
            cands.append((inv.fin_estac, self.PRIORIDAD["FE"], "FE", inv))
        for k in (0, 1):
            if self.fin_acred[k] is not None:
                cod = f"FAO{k + 1}"
                cands.append((self.fin_acred[k], self.PRIORIDAD[cod], cod, k))
        if self.fin_qr is not None:
            cands.append((self.fin_qr, self.PRIORIDAD["FQR"], "FQR", None))
        if self.fin_rec is not None:
            cands.append((self.fin_rec, self.PRIORIDAD["FAR"], "FAR", None))
        return min(cands, key=lambda c: (c[0], c[1]))

    def _avanzar_reloj(self, t):
        """Acumula los tiempos que dependen del estado ANTERIOR y mueve el reloj."""
        dt = t - self.reloj
        if self.rec_estado == LIBRE:
            self.ac_libre_rec += dt
        if self.qr_estado == OCUPADO:
            self.ac_ocup_qr += dt
        self.reloj = t
        self.n += 1

    def _procesar(self, t, codigo, obj):
        self._avanzar_reloj(t)
        f = {}
        if codigo == "LLA":
            self._llegada_auto(f)
        elif codigo in ("FAO1", "FAO2"):
            self._fin_acred_porton(obj, f)
        elif codigo == "FE":
            self._fin_estacionamiento(obj, f)
        elif codigo == "LLP":
            self._llegada_peaton(f)
        elif codigo == "FQR":
            self._fin_escaneo_qr(f)
        elif codigo == "FAR":
            self._fin_acred_recep(f)
        elif codigo == "FD":
            self._fin_degustacion(obj, f)
        return f

    def _fila_completa(self, f, con_temporales=True):
        """Arma la fila del vector de estado con el estado actual."""
        r = dict.fromkeys(COLUMNAS_FIJAS)
        r.update(f)
        r["Fila"] = self.n
        r["Reloj"] = self.reloj
        r["Próx. lleg. auto"] = self.prox_lleg_auto
        r["Fin acred. Op1"] = self.fin_acred[0]
        r["Fin acred. Op2"] = self.fin_acred[1]
        r["Próx. fin estac."] = (min(i.fin_estac for i in self.estacionando)
                                 if self.estacionando else None)
        r["Próx. lleg. peatón"] = self.prox_lleg_peaton
        r["Fin escaneo QR"] = self.fin_qr
        r["Fin acred. recep."] = self.fin_rec
        r["Próx. fin degust."] = (min(i.fin_deg for i in self.en_sala)
                                  if self.en_sala else None)
        r["Op1 estado"], r["Op2 estado"] = self.op_estado
        r["Cola portón"] = len(self.cola_porton)
        r["QR estado"] = self.qr_estado
        r["Cola QR"] = len(self.cola_qr)
        r["Recep. estado"] = self.rec_estado
        r["Cola recep."] = len(self.cola_rec)
        r["Cant. estacionando"] = len(self.estacionando)
        r["Cant. en sala"] = len(self.en_sala)

        r["AC t libre recep."] = self.ac_libre_rec
        r["% t libre recep."] = (self.ac_libre_rec / self.reloj * 100) if self.reloj > 0 else None
        r["AC t ocupado QR"] = self.ac_ocup_qr
        r["% uso QR"] = (self.ac_ocup_qr / self.reloj * 100) if self.reloj > 0 else None
        r["AC demora AP"] = self.ac_demora_ap
        r["Cant. acreditados AP"] = self.cant_acred_ap
        r["Prom. demora AP"] = (self.ac_demora_ap / self.cant_acred_ap) if self.cant_acred_ap else None
        r["AC espera cola AP"] = self.ac_espera_ap
        r["Cant. inician atención AP"] = self.cant_inicio_ap
        r["Prom. espera cola AP"] = (self.ac_espera_ap / self.cant_inicio_ap) if self.cant_inicio_ap else None
        r["AC permanencia"] = self.ac_perm
        r["Cant. salidas"] = self.cant_salidas
        r["Prom. permanencia"] = (self.ac_perm / self.cant_salidas) if self.cant_salidas else None

        if con_temporales:
            r["_temporales"] = [(inv.clase, inv.id, inv.nombre, inv.atributos())
                                for inv in self.vivos.values()]
        return r

    def ejecutar(self):
        p = self.p
        X, N = p["tiempo_X"], p["max_iteraciones"]
        i_mostrar, j_hora = p["mostrar_i"], p["desde_hora_j"]
        filas_mostradas = []

        def quizas_guardar(f):
            # Solo se guardan las i filas pedidas a partir de la hora j
            if len(filas_mostradas) < i_mostrar and self.reloj >= j_hora:
                filas_mostradas.append(self._fila_completa(f, True))

        f = self._inicializar()
        quizas_guardar(f)

        while True:
            if self.n >= N:
                motivo = f"Se alcanzó el máximo de {N:,} iteraciones (reloj = {self.reloj:.4f})"
                ultima = self._fila_completa(f, False)
                break
            t, _, codigo, obj = self._proximo_evento()
            if t > X:
                # Última fila: el instante X
                self._avanzar_reloj(X)
                f = {"Evento": "Fin simulación (X)"}
                quizas_guardar(f)
                motivo = f"Se alcanzó el tiempo X = {X:,} min"
                ultima = self._fila_completa(f, False)
                break
            f = self._procesar(t, codigo, obj)
            quizas_guardar(f)

        estimadores = {
            "prom_demora_ap": ultima["Prom. demora AP"],
            "prom_espera_ap": ultima["Prom. espera cola AP"],
            "porc_libre_rec": ultima["% t libre recep."],
            "porc_uso_qr": ultima["% uso QR"],
            "prom_permanencia": ultima["Prom. permanencia"],
            "reloj_final": self.reloj,
            "iteraciones": self.n,
            "motivo": motivo,
            "llegados_iv": self.cont_iv,
            "llegados_ip": self.cont_ip,
            "cant_qr": self.cant_qr,
            "cant_presencial": self.cant_presencial,
            "cant_salidas": self.cant_salidas,
            "acreditados_ap": self.cant_acred_ap,
            "rnd_usados": self.gen.usados,
            "en_sistema_al_final": len(self.vivos),
        }
        return {
            "filas_mostradas": filas_mostradas,
            "ultima": ultima,
            "estimadores": estimadores,
            "tablas_euler": self.tablas_euler,
            "rangos_exp": self.rangos_exp,
            "periodo": periodo_generador(p["semilla"], p["a"], p["c"], p["m"]),
        }


def simular(p):
    return Simulacion(p).ejecutar()


# ---------------------------------------------------------------------------
# 8) ARMADO DE LA TABLA DEL VECTOR (sin pandas)
# ---------------------------------------------------------------------------
def columnas_temporales(filas):
    """
    Junta todos los objetos temporales que aparecen en las filas mostradas
    y arma sus columnas: primero los IV (por número) y después los IP.
    """
    presentes = {}
    for r in filas:
        for clase, id_, nombre, _ in r.get("_temporales", []):
            presentes[nombre] = (0 if clase == "IV" else 1, id_, clase)
    orden = sorted(presentes.items(), key=lambda kv: (kv[1][0], kv[1][1]))
    cols = []
    for nombre, (_, _, clase) in orden:
        for atr in ATRIBUTOS_TEMPORALES[clase]:
            cols.append((nombre, atr, f"{nombre} {atr}"))
    return cols


def filas_planas(filas, incluir_temporales=True):
    """Devuelve (lista de nombres de columna, lista de filas como dict)."""
    cols_t = columnas_temporales(filas) if incluir_temporales else []
    nombres = COLUMNAS_FIJAS + [c[2] for c in cols_t]
    salida = []
    for r in filas:
        d = {c: r.get(c) for c in COLUMNAS_FIJAS}
        if incluir_temporales:
            vivos = {nombre: atrs for _, _, nombre, atrs in r.get("_temporales", [])}
            for nombre, atr, col in cols_t:
                d[col] = vivos[nombre][atr] if nombre in vivos else None
        salida.append(d)
    return nombres, salida
