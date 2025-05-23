import streamlit as st
import openai

st.set_page_config(page_title="Certificazione Team Work", layout="centered")

# Inizializza stato
if "step" not in st.session_state:
    st.session_state.step = "profilo"
    st.session_state.profilo_utente = {}
    st.session_state.domande = []
    st.session_state.indice = 0
    st.session_state.risposte = []
    st.session_state.punteggi = []
    st.session_state.valutazioni = []

# Prompt iniziale
def genera_prompt_iniziale(profilo):
    return f"""Sei un esperto psicologo del lavoro. In base al seguente profilo:

Nome: {profilo['nome']}
Età: {profilo['eta']}
Azienda: {profilo['azienda']}
Settore: {profilo['settore']}
Ruolo: {profilo['ruolo']}
Esperienza nel settore: {profilo['anni_settore']}
Esperienza nel ruolo: {profilo['anni_ruolo']}

Genera una domanda per valutare il teamwork. Deve essere situazionale e realistica."""

# Prompt domanda successiva
def genera_domanda_dinamica(profilo, storia_risposte):
    contesto = "\n".join([f"D: {d}\nR: {r}" for d, r in storia_risposte])
    prompt = f"""In base a questo profilo:

Nome: {profilo['nome']}, Età: {profilo['eta']}, Azienda: {profilo['azienda']}, Settore: {profilo['settore']}, Ruolo: {profilo['ruolo']}, Esperienza nel settore: {profilo['anni_settore']}, Esperienza nel ruolo: {profilo['anni_ruolo']}

Ecco alcune risposte precedenti:
{contesto}

Genera una nuova domanda di valutazione del teamwork per continuare l’assessment. Deve esplorare meglio eventuali incoerenze o approfondire nuovi aspetti. Domanda situazionale, scrivi solo la domanda senza spiegazioni, né premesse, né introduzioni."""

    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# Valutazione risposta
def valuta_risposta(risposta):
    prompt = f"""Valuta questa risposta rispetto al lavoro in team.

Risposta: "{risposta}"

Assegna un punteggio da 0 a 100 per:
- Collaborazione
- Comunicazione
- Leadership
- Problem solving
- Empatia

Rispondi così:
Collaborazione: XX
Comunicazione: XX
Leadership: XX
Problem solving: XX
Empatia: XX

Motiva brevemente ciascun punteggio."""
    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# Fase 1: Profilo
if st.session_state.step == "profilo":
    st.title("Certificazione Team Work – Profilo iniziale")
    nome = st.text_input("Nome e cognome")
    eta = st.number_input("Età", min_value=16, max_value=99)
    azienda = st.text_input("Azienda attuale o precedente")
    settore = st.text_input("Settore di attività")
    ruolo = st.text_input("Ruolo")
    anni_settore = st.slider("Anni esperienza settore", 0, 40, 5)
    anni_ruolo = st.slider("Anni esperienza ruolo", 0, 40, 3)

    if st.button("Inizia il test"):
        if all([nome, eta, azienda, settore, ruolo]):
            st.session_state.profilo_utente = {
                "nome": nome,
                "eta": eta,
                "azienda": azienda,
                "settore": settore,
                "ruolo": ruolo,
                "anni_settore": anni_settore,
                "anni_ruolo": anni_ruolo
            }
            prompt = genera_prompt_iniziale(st.session_state.profilo_utente)
            out = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            st.session_state.domande = [out.choices[0].message.content.strip()]
            st.session_state.indice = 0
            st.session_state.step = "test"
            st.rerun()
        else:
            st.error("Compila tutti i campi.")

# Fase 2: Test
elif st.session_state.step == "test":
    st.title("Domande dinamiche di Team Work")
    indice = st.session_state.indice

    if indice >= len(st.session_state.domande):
        nuova = genera_domanda_dinamica(
            st.session_state.profilo_utente,
            list(zip(st.session_state.domande, st.session_state.risposte))
        )
        st.session_state.domande.append(nuova)

    domanda = st.session_state.domande[indice]
    st.markdown(f"**Domanda {indice + 1} di 40**")
    st.markdown(f"> {domanda}")

    risposta = st.text_area("La tua risposta", key=f"risposta_{indice}")

    if st.button("Invia risposta"):
        st.session_state.risposte.append(risposta)

        valutazione = valuta_risposta(risposta)
        st.session_state.valutazioni.append(valutazione)

        punteggi = {}
        for line in valutazione.splitlines():
            for k in ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]:
                if line.startswith(k):
                    try:
                        punteggi[k] = int("".join(filter(str.isdigit, line)))
                    except:
                        pass
        st.session_state.punteggi.append(punteggi)

        st.session_state.indice += 1

        if st.session_state.indice == 40:
            st.session_state.step = "risultato"

        st.rerun()


# Fase 3: Risultato
elif st.session_state.step == "risultato":
    st.title("✅ Profilazione completata")

    media = {}
    for k in ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]:
        punteggi_k = [p.get(k, 0) for p in st.session_state.punteggi if k in p]
        media[k] = round(sum(punteggi_k)/len(punteggi_k), 2)

    totale = round(sum(media.values()) / len(media), 2)

    st.markdown("### Profilo finale:")
    for k, v in media.items():
        st.markdown(f"**{k}:** {v}/100")

    st.markdown("### 🧭 Esito certificazione")
    if totale >= 70:
        st.success("🎖 Complimenti! Hai ottenuto la certificazione Team Work")
        st.image("https://raw.githubusercontent.com/CertSkill/teamwork-cert/main/badge.png", width=300)
    else:
        st.warning("Continua ad allenarti per ottenere la certificazione.")

    if st.button("🔄 Ricomincia il test"):
        st.session_state.clear()
        st.rerun()
