# Segurança temporal da criptografia RSA

Demonstração visual (Streamlit) do exercício de **complexidade / segurança temporal**
da pós-graduação em Criptografia.

O programa mostra, na prática, que encriptar *poucos* plaintexts é instantâneo,
mas varrer um espaço de mensagens da ordem de $n$ torna-se **inviável no tempo**.

---

## Uso rápido

### Pré-requisitos

- [uv](https://docs.astral.sh/uv/) instalado
- Python 3.12+ (o `uv` resolve automaticamente)

### Instalar e executar

```bash
cd crypto_complexity
uv sync
uv run streamlit run app.py
```

O navegador abre em `http://localhost:8501`.

### Fluxo sugerido em aula (≈ 5–10 min)

| Passo | Botão / ação | O que observar |
|------|--------------|----------------|
| 1 | **Gerar p, q e n** | Primo de 10 dígitos × primo de 11 dígitos → $n \\approx 10^{20}$–$10^{21}$ |
| 2 | **Executar item (b)** | $9999$ encriptações em $n_1,n_2,n_3$ — quase instantâneo; resultados **não** são guardados |
| 3 | **Executar item (c)** | Preferir modo **Automático** (escolhe $10^7$ / $10^8$ / $10^9$); anotar o tempo medido |
| 4 | Ver **item (d)** | Extrapolação linear para $1 \\le m < n$ em **anos** ($1$ ano $\\approx 3\\times 10^7$ s) |

Mensagem pedagógica: *a operação RSA individual é rápida; o espaço completo de mensagens não é.*

---

## Itens do enunciado cobertos

### (a) Geração de módulo

- Gera primo $p$ com **10 dígitos** e primo $q$ com **11 dígitos**
- Forma $n = pq$
- Exibe $p$, $q$ e $n$ na interface

### (b) Encriptação em lote (rápida)

- Expoente $e = 65537$
- Para cada $n \\in \\{n_1, n_2, n_3\\}$ do enunciado:
  - $n_1 = 2469247531693$
  - $n_2 = 11111502225583$
  - $n_3 = 44444222221411$
- Calcula $c = m^e \\bmod n$ para todos $1 \\le m < 10^4$
- **Não armazena nem exibe** os ciphertexts — apenas o tempo e a taxa

### (c) Endurecimento + medição

- Repete o laço com $m_{\\max} \\in \\{10^7, 10^8, 10^9\\}$
- Modo **Automático**: amostra rápida → escolhe o maior limite ainda mensurável
- Barra de progresso durante a medição

### (d) Estimativa para o espaço completo

$$
T(n) \\approx T(m_{\\max}) \\cdot \\frac{n-1}{m_{\\max}-1}
$$

- Converte o resultado para anos com $3 \\times 10^7$ s/ano
- Permite estimar sobre o $n$ medido, $n_1$–$n_3$ ou o $n$ gerado no item (a)

---

## Estrutura do projeto

```
crypto_complexity/
├── app.py              # Interface Streamlit (itens a–d)
├── rsa_timing.py       # Geração de primos, encriptação, timing, extrapolação
├── pyproject.toml      # Dependências geridas pelo uv
├── uv.lock             # Lockfile reproduzível
└── README.md           # Este arquivo
```

| Arquivo | Papel |
|---------|--------|
| `app.py` | UI didática passo a passo |
| `rsa_timing.py` | Lógica pura (fácil de revisar / testar sem Streamlit) |

---

## Dependências

| Pacote | Uso |
|--------|-----|
| `streamlit` | Interface visual |
| `sympy` | Geração de primos (`randprime`) |

Gerenciadas exclusivamente via **uv** (`uv sync` / `uv add`).

---

## Notas técnicas (avaliação / correção)

1. **Encriptação RSA:** `pow(m, e, n)` — exponenciação modular nativa do Python (equivalente a $m^e \\bmod n$).
2. **Sem persistência de ciphertexts:** o laço descarta o retorno de cada `pow` (conforme enunciado).
3. **Tempo:** `time.perf_counter()` (relógio monotônico de alta resolução).
4. **Extrapolação:** linear no número de plaintexts; assume custo médio constante por encriptação (razoável para $m < n$ e $n$ fixo).
5. **Item (c) longo:** $10^8$ ou $10^9$ pode levar minutos. Em aula, use o modo **Automático** ou $10^7$.

---

## Comandos úteis

```bash
# Instalar dependências
uv sync

# Rodar a demo
uv run streamlit run app.py

# Porta alternativa
uv run streamlit run app.py --server.port 8502
```

---

## Autoria / contexto

Material de apoio ao exercício de **segurança temporal** do módulo de Criptografia
(pós-graduação). Destinado a demonstração em aula e verificação rápida pelo docente.
