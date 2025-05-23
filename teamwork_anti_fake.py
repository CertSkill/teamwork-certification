
import streamlit as st
import openai

st.set_page_config(page_title="Certificazione Team Work – Anti-manipolazione", layout="centered")
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("Certificazione Team Work – Sistema Adattivo e Coerente")

# Inizializzazione
if "fase" not in st.session_state:
    st.session_state.fase = "anagrafica"
    st.session_state.profilo_utente = {}
    st.session_state.domande = []
    st.session_state.risposte = []
    st.session_state.comportamenti = []
    st.session_state.indice_domanda = 0
    st.session_state.max_domande = 40
    st.session_state.profilo_valutato = False
    st.session_state.risultato_finale = ""

# Step 1 – Profilo
if st.session_state.fase == "anagrafica":
    with st.form("profilo_utente"):
        nome = st.text_input("Nome e Cognome")
        eta = st.number_input("Età", 16, 100)
        azienda = st.text_input("Azienda attuale o precedente")
        settore = st.text_input("Settore (es. Sanità)")
        ruolo = st.text_input("Ruolo attuale o precedente")
        anni_settore = st.number_input("Anni esperienza settore", 0, 50)
        anni_ruolo = st.number_input("Anni esperienza ruolo", 0, 50)
        submitted = st.form_submit_button("Inizia il test")

        if submitted and nome and settore and ruolo:
            st.session_state.profilo_utente = {
                "nome": nome,
                "eta": eta,
                "azienda": azienda,
                "settore": settore,
                "ruolo": ruolo,
                "anni_settore": anni_settore,
                "anni_ruolo": anni_ruolo
            }
            st.session_state.fase = "test"
            st.rerun()

# Funzione generazione domanda con dilemmi e incoerenze
def genera_domanda_anti_fake(risposte_precedenti):
    profilo = st.session_state.profilo_utente
    prompt = f"""
Sei un team di esperti psicologi (Mayo, Lewin, Herzberg, Spector).
Analizza le seguenti risposte fornite da un candidato:

{risposte_precedenti}

Ora genera una nuova domanda per valutare teamwork in situazioni reali, includendo:
- dilemmi etici o ambigui
- situazioni da colloquio simulate
- possibile contraddizione con risposte precedenti

Scegli tra: comunicazione, empatia, conflitto, collaborazione, leadership.

Scrivi solo la domanda.
"""
    out = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return out.choices[0].message.content.strip()

# Analisi del comportamento
def classifica_comportamento(risposta):
    prompt = f"""
Analizza questa risposta:
"{risposta}"
Classifica lo stile comportamentale: Cooperativo, Assertivo, Evasivo, Conflittuale, Passivo, Diplomatico, Opportunista.

Rispondi con:
Stile: [etichetta]
Motivazione: [breve motivazione]
"""
    result = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return result.choices[0].message.content.strip()

# Valutazione finale
def valuta_teamwork(risposte, comportamenti):
    profilo = st.session_state.profilo_utente
    storia = "\n".join([f"Domanda: {q}\nRisposta: {a}\nComportamento: {c}" for q, a, c in zip(st.session_state.domande, risposte, comportamenti)])
    prompt = f"""
Analizza le seguenti risposte per valutare il teamwork:

{storia}

Assegna punteggi da 0 a 100 su:
- Collaborazione
- Comunicazione
- Gestione dei conflitti
- Leadership diffusa
- Empatia

Indica media, punti forti, aree deboli. Se media >=70, consiglia badge.
"""
    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# Fase test
if st.session_state.fase == "test":
    if st.session_state.indice_domanda < st.session_state.max_domande:
        if st.session_state.indice_domanda == 0 or len(st.session_state.domande) <= st.session_state.indice_domanda:
            storia = "\n".join([f"Domanda: {d}\nRisposta: {r}" for d, r in zip(st.session_state.domande, st.session_state.risposte)])
            nuova_domanda = genera_domanda_anti_fake(storia)
            st.session_state.domande.append(nuova_domanda)

        st.markdown(f"### Domanda {st.session_state.indice_domanda + 1}")
        st.markdown(st.session_state.domande[st.session_state.indice_domanda])
        risposta = st.text_area("La tua risposta", value="", key=f"r_{st.session_state.indice_domanda}")

        if st.button("Invia", key=f"b_{st.session_state.indice_domanda}"):
            if risposta.strip():
                st.session_state.risposte.append(risposta.strip())
                comportamento = classifica_comportamento(risposta.strip())
                st.session_state.comportamenti.append(comportamento)
                st.session_state.indice_domanda += 1
                if st.session_state.indice_domanda >= 25:
                    st.session_state.profilo_valutato = True
                st.rerun()

# Fase finale
if st.session_state.profilo_valutato and st.session_state.indice_domanda >= 25:
    st.markdown("## ✅ Test completato")
    if not st.session_state.risultato_finale:
        with st.spinner("Analisi finale in corso..."):
            st.session_state.risultato_finale = valuta_teamwork(st.session_state.risposte, st.session_state.comportamenti)

    st.markdown("### 📊 Profilo del candidato")
    st.text(st.session_state.risultato_finale)

    if ">=70" in st.session_state.risultato_finale or "maggiore di 70" in st.session_state.risultato_finale:
        st.image("https://raw.githubusercontent.com/CertSkill/teamwork-cert/main/badge.png", width=300)
        st.success("🎖 Hai ottenuto la certificazione Team Work!")
    else:
        st.info("🧠 Continua ad allenarti per ottenere il badge.")

    if st.button("🔁 Ricomincia"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
