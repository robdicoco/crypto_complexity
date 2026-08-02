"""
Streamlit demo — Temporal security of RSA (postgraduate cryptography exercise).

Shows: prime generation → bulk encryption → timed hardening → full-space estimate.
"""

from __future__ import annotations

import math

import streamlit as st

from rsa_timing import (
    E,
    EXERCISE_MODULI,
    SECONDS_PER_YEAR,
    calibrate_m_max,
    digit_count,
    estimate_full_space_time,
    format_duration,
    generate_rsa_modulus,
    time_encrypt_range,
)

st.set_page_config(
    page_title="RSA — Segurança Temporal",
    page_icon="🔐",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "primes" not in st.session_state:
    st.session_state.primes = None
if "item_b" not in st.session_state:
    st.session_state.item_b = None
if "item_c" not in st.session_state:
    st.session_state.item_c = None


def _progress_bar():
    bar = st.progress(0.0, text="Criptografando…")

    def update(done: int, total: int) -> None:
        frac = done / total if total else 1.0
        bar.progress(min(frac, 1.0), text=f"Criptografando… {done:,} / {total:,}")

    return bar, update


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Segurança temporal da criptografia RSA")
st.caption(
    "Exercício de pós-graduação — complexidade da encriptação exaustiva do espaço de mensagens."
)

with st.expander("Sobre este programa (para o professor)", expanded=False):
    st.markdown(
        """
Este aplicativo reproduz visualmente o exercício de **segurança temporal** do RSA:

1. **Item (a)** — gera um primo $p$ com 10 dígitos e um primo $q$ com 11 dígitos; forma $n = pq$.
2. **Item (b)** — com $e = 65537$, calcula $c = m^e \\bmod n$ para todos os plaintexts
   $1 \\le m < 10^4$ nos módulos $n_1$, $n_2$ e $n_3$ do enunciado.
   **Não armazena nem exibe** os resultados.
3. **Item (c)** — endurece o teste para $10^7$, $10^8$ ou $10^9$ e **mede o tempo**.
4. **Item (d)** — estima, por extrapolação linear, quanto tempo levaria criptografar
   todos os $m$ com $1 \\le m < n$ (usando $\\approx 3 \\times 10^7$ segundos por ano).

**Como executar:** `uv sync` e depois `uv run streamlit run app.py`
        """
    )

st.divider()

# ===========================================================================
# ITEM (a) — Generate primes
# ===========================================================================
st.header("Item (a) — Geração de $p$, $q$ e $n = pq$")
st.markdown(
    "Gere **um primo $p$ com 10 dígitos** e **um primo $q$ com 11 dígitos**, "
    "depois forme $n = pq$."
)

if st.button("Gerar $p$, $q$ e $n$", type="primary", key="btn_a"):
    with st.spinner("Gerando primos…"):
        p, q, n = generate_rsa_modulus(10, 11)
    st.session_state.primes = {"p": p, "q": q, "n": n}
    # New modulus invalidates previous timings that depended on demo n
    st.session_state.item_c = None

if st.session_state.primes:
    p = st.session_state.primes["p"]
    q = st.session_state.primes["q"]
    n = st.session_state.primes["n"]
    c1, c2, c3 = st.columns(3)
    c1.metric(f"$p$ ({digit_count(p)} dígitos)", f"{p}")
    c2.metric(f"$q$ ({digit_count(q)} dígitos)", f"{q}")
    c3.metric(f"$n = pq$ ({digit_count(n)} dígitos)", f"{n}")
    st.success(f"$n = {p} \\times {q} = {n}$")
else:
    st.info("Clique no botão acima para gerar os primos.")

st.divider()

# ===========================================================================
# ITEM (b) — Encrypt m < 10^4 (instant)
# ===========================================================================
st.header("Item (b) — Encriptações RSA com $1 \\le m < 10^4$")
st.markdown(
    f"""
Expoente de criptografia: **$e = {E}$**.

Calcule as encriptações RSA de todos os plaintexts $m$ tais que $1 \\le m < 10^4$.

**Não armazene nem exiba os resultados.** O computador provavelmente fará isso quase instantaneamente.

Módulos do enunciado:
"""
)
cols = st.columns(3)
for col, (name, value) in zip(cols, EXERCISE_MODULI.items()):
    col.code(f"{name} = {value}")

if st.button("Executar item (b)", type="primary", key="btn_b"):
    results = {}
    with st.spinner("Criptografando (sem armazenar resultados)…"):
        for name, modulus in EXERCISE_MODULI.items():
            tr = time_encrypt_range(modulus, E, 10**4)
            results[name] = tr
    st.session_state.item_b = results

if st.session_state.item_b:
    st.success(
        "Concluído. Resultados **não foram armazenados nem exibidos** "
        "(apenas o tempo de execução)."
    )
    rows = []
    for name, tr in st.session_state.item_b.items():
        rows.append(
            {
                "módulo": name,
                "n": tr.n,
                "plaintexts": f"1 … {tr.m_max - 1}",
                "encriptações": tr.encryptions,
                "tempo": format_duration(tr.elapsed_seconds),
                "taxa (enc/s)": f"{tr.rate:,.0f}",
            }
        )
    st.dataframe(rows, hide_index=True, use_container_width=True)
    st.caption(
        "Observe que $10^4 - 1 = 9999$ encriptações terminam quase instantaneamente — "
        "ainda não dá para sentir o custo real do espaço de mensagens."
    )

st.divider()

# ===========================================================================
# ITEM (c) — Hardening + wall-clock measurement
# ===========================================================================
st.header("Item (c) — Endurecimento: medir o tempo")
st.markdown(
    """
Repita o programa do item (b) para criptografar todos os $m$ tais que
$1 \\le m < 10^8$, e **meça quanto tempo isso leva**.

- Se demorar demais, use $10^7$.
- Se for rápido demais para medir, use $10^9$.
"""
)

target_choice = st.radio(
    "Limite superior de $m$ ($m_{\\max}$)",
    options=["auto", 10**7, 10**8, 10**9],
    format_func=lambda x: (
        "Automático (escolhe entre $10^7$, $10^8$, $10^9$)"
        if x == "auto"
        else f"$10^{{{len(str(x))-1}}}$ = {x:,}"
    ),
    horizontal=True,
)

modulus_source = st.radio(
    "Módulo $n$ usado na medição",
    options=["n1", "n2", "n3", "generated"],
    format_func=lambda x: (
        f"n gerado no item (a)"
        if x == "generated"
        else f"{x} = {EXERCISE_MODULI[x]:,}"
    ),
    horizontal=True,
)

if modulus_source == "generated":
    if not st.session_state.primes:
        st.warning("Gere $n$ no item (a) antes, ou escolha $n_1$, $n_2$ ou $n_3$.")
        n_c = None
    else:
        n_c = st.session_state.primes["n"]
else:
    n_c = EXERCISE_MODULI[modulus_source]

run_c = st.button(
    "Executar item (c) e medir tempo",
    type="primary",
    key="btn_c",
    disabled=n_c is None,
)

if run_c and n_c is not None:
    if target_choice == "auto":
        with st.spinner("Calibrando $m_{\\max}$ com amostra rápida…"):
            m_max = calibrate_m_max(n_c, E)
        st.info(f"Modo automático escolheu $m_{{\\max}} = {m_max:,}$.")
    else:
        m_max = int(target_choice)

    bar, on_progress = _progress_bar()
    try:
        tr = time_encrypt_range(
            n_c,
            E,
            m_max,
            progress_callback=on_progress,
            progress_every=max(m_max // 200, 10_000),
        )
    finally:
        bar.empty()

    st.session_state.item_c = {
        "result": tr,
        "label": modulus_source,
    }

if st.session_state.item_c:
    tr = st.session_state.item_c["result"]
    label = st.session_state.item_c["label"]
    st.success("Medição concluída.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Módulo", label)
    m2.metric("$m_{\\max}$", f"{tr.m_max:,}")
    m3.metric("Tempo medido", format_duration(tr.elapsed_seconds))
    m4.metric("Taxa", f"{tr.rate:,.0f} enc/s")
    st.markdown(
        f"""
**Detalhe:** ${tr.encryptions:,}$ encriptações RSA ($e = {E}$) em
**{tr.elapsed_seconds:.4f} s** sobre $n = {tr.n}$.
        """
    )

st.divider()

# ===========================================================================
# ITEM (d) — Extrapolate to full message space
# ===========================================================================
st.header("Item (d) — Estimativa para $1 \\le m < n$")
st.markdown(
    f"""
Usando a medição de tempo do item (c), estime quanto tempo levaria para
criptografar **todos** os $m$ tais que $1 \\le m < n$.

Um ano tem aproximadamente **${SECONDS_PER_YEAR:.0e}$ segundos** ($3 \\times 10^7$).

Hipótese de extrapolação (linear):

$$
T(n) \\approx T(m_{{\\max}}) \\cdot \\frac{{n - 1}}{{m_{{\\max}} - 1}}
$$
"""
)

if not st.session_state.item_c:
    st.warning("Execute o item (c) primeiro para obter a medição de tempo.")
else:
    tr = st.session_state.item_c["result"]
    st.markdown(
        f"Medição base: **{tr.encryptions:,}** encriptações em "
        f"**{tr.elapsed_seconds:.4f} s** "
        f"(taxa ≈ **{tr.rate:,.0f}** enc/s)."
    )

    targets: list[tuple[str, int]] = [
        ("n da medição (c)", tr.n),
        ("n1", EXERCISE_MODULI["n1"]),
        ("n2", EXERCISE_MODULI["n2"]),
        ("n3", EXERCISE_MODULI["n3"]),
    ]
    if st.session_state.primes:
        targets.append(("n do item (a)", st.session_state.primes["n"]))

    rows = []
    chart_labels = []
    chart_log_years = []
    for label, target_n in targets:
        est = estimate_full_space_time(tr, target_n)
        rows.append(
            {
                "rótulo": label,
                "n": str(target_n),
                "dígitos de n": digit_count(target_n),
                "encriptações (n−1)": f"{target_n - 1:,}",
                "tempo estimado": format_duration(est["seconds"]),
                "anos (≈)": f"{est['years']:.3e}",
            }
        )
        chart_labels.append(label)
        # log10(years) for readable comparison across orders of magnitude
        chart_log_years.append(math.log10(max(est["years"], 1e-30)))

    st.subheader("Estimativas")
    st.dataframe(rows, hide_index=True, use_container_width=True)

    # Highlight the largest n (usually item a) as the pedagogical punchline
    focus_label, focus_n = targets[-1]
    focus = estimate_full_space_time(tr, focus_n)
    f1, f2, f3 = st.columns(3)
    f1.metric("Foco", focus_label)
    f2.metric("Tempo estimado", format_duration(focus["seconds"]))
    f3.metric("Em anos", f"{focus['years']:.3e}")

    st.markdown("#### Comparação (escala $\\log_{{10}}$ dos anos)")
    st.bar_chart(
        {"módulo": chart_labels, "log₁₀(anos)": chart_log_years},
        x="módulo",
        y="log₁₀(anos)",
        horizontal=True,
    )
    st.caption(
        f"Referência do enunciado: $1$ ano $\\approx {SECONDS_PER_YEAR:.0e}$ s. "
        "Valores negativos em $\\log_{{10}}$ significam fração de ano."
    )

    st.markdown(
        """
#### Interpretação pedagógica

Cada encriptação RSA ($m^e \\bmod n$) é **rápida**. Porém, criptografar
**todos** os plaintexts $1 \\le m < n$ escala com o tamanho de $n$.
Para o $n$ gerado no item (a) (cerca de 21 dígitos), a extrapolação costuma
indicar **milhões ou bilhões de anos** — segurança temporal por complexidade
do espaço de mensagens, não pela lentidão de uma operação isolada.
        """
    )

st.divider()
st.caption(
    "crypto_complexity · demonstração didática de complexidade temporal do RSA · "
    "pós-graduação em Criptografia"
)
