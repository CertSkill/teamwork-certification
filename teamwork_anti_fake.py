import streamlit as st
import openai

st.set_page_config(page_title="Certificazione Team Work", layout="centered")

# Inizializzazione variabili sessione
if "step" not in st.session_state:
    st.session_state.step = "profilo"
    st.session_state.profilo_utente = {}
    st.session_state.domande = []
    st.session_state.indice = 0
    st.session_state.risposte = []
    st.session_state.punteggi = []
    st.session_state.valutazioni = []

# Funzione per creare il prompt iniziale
def genera_prompt_iniziale(profilo):
    return f"""Sei un esperto psicologo del lavoro e recruiter. In base al seguente profilo:

Nome: {profilo['nome']}
Età: {profilo['eta']}
Azienda: {profilo['azienda']}
Settore: {profilo['settore']}
Ruolo: {profilo['ruolo']}
Anni di esperienza nel settore: {profilo['anni_settore']}
Anni di esperienza nel ruolo: {profilo['anni_ruolo']}

Genera la prima di una serie di domande per valutare il teamwork. Le domande devono essere realistiche, situazionali e valutare dinamiche di gruppo, responsabilità, empatia, conflitto o collaborazione. Scrivi solo la domanda, senza altro testo."""

# Funzione per generare una nuova domanda dinamica
def genera_domanda_dinamica(profilo, storia_risposte):
    contesto = "\n".join([f"D: {d}\nR: {r}" for d, r in storia_risposte])
    return f"""In base a questo profilo:

Nome: {profilo['nome']}, Età: {profilo['eta']}, Azienda: {profilo['azienda']}, Settore: {profilo['settore']}, Ruolo: {profilo['ruolo']}, Esperienza nel settore: {profilo['anni_settore']}, Esperienza nel ruolo: {profilo['anni_ruolo']}

Ecco alcune risposte precedenti:
{contesto}

Genera una nuova domanda di valutazione del teamwork per continuare l’assessment. Deve esplorare meglio eventuali incoerenze o approfondire nuovi aspetti. Scrivi solo la domanda."""

# Funzione per valutare la risposta
def valuta_risposta(risposta):
    prompt = f"""Valuta questa risposta in un contesto di lavoro in team.
Risposta: "{risposta}"

Assegna un punteggio da 0 a 100 per:
- Collaborazione
- Comunicazione
- Leadership
- Problem solving
- Empatia

Scrivi nel formato:
Collaborazione: XX
Comunicazione: XX
Leadership: XX
Problem solving: XX
Empatia: XX

Spiega brevemente perché per ogni punteggio."""
    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# --- FASE 1: Raccolta dati profilo utente ---
if st.session_state.step == "profilo":
    st.title("Certificazione Team Work – Sistema Adattivo e Coerente")
    st.subheader("Compila il tuo profilo per iniziare")

    nome = st.text_input("Nome e cognome")
    eta = st.number_input("Età", min_value=16, max_value=99, step=1)
    azienda = st.text_input("Azienda attuale o più recente")
    settore = st.text_input("Settore di attività")
    ruolo = st.text_input("Ruolo attuale o più recente")
    anni_settore = st.slider("Anni di esperienza nel settore", 0, 40, 5)
    anni_ruolo = st.slider("Anni di esperienza nel ruolo", 0, 40, 3)

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

        # Genera prima domanda
        prompt = genera_prompt_iniziale(st.session_state.profilo_utente)
        risposta_openai = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        domanda = risposta_openai.choices[0].message.content.strip()

        st.session_state.domande = [domanda]
        st.session_state.indice = 0
        st.session_state.step = "test"
        st.rerun()
    else:
        st.error("Compila tutti i campi prima di iniziare il test.")

# --- FASE 2: Domande dinamiche e valutazione ---
elif st.session_state.step == "test":
    st.title("Domande dinamiche di Team Work")
    indice = st.session_state.indice
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

        if st.session_state.indice >= 25 and st.session_state.indice < 40:
            profilo = st.session_state.profilo_utente
            storia = list(zip(st.session_state.domande, st.session_state.risposte))
            nuova = genera_domanda_dinamica(profilo, storia)
            st.session_state.domande.append(nuova)
        elif st.session_state.indice == 40:
            st.session_state.step = "risultato"

        st.rerun()

# --- FASE 3: Profilo finale e badge ---
elif st.session_state.step == "risultato":
    st.title("✅ Profilazione completata")

    media = {}
    for k in ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]:
        valori = [p.get(k, 0) for p in st.session_state.punteggi if k in p]
        media[k] = round(sum(valori)/len(valori), 2)

    totale = round(sum(media.values()) / len(media), 2)

    st.markdown("### Profilo finale:")
    for k, v in media.items():
        st.markdown(f"**{k}**: {v}/100")

    st.markdown("### 🧭 Esito certificazione")
    if totale >= 70:
        st.success("🎖 Complimenti! Hai ottenuto la certificazione Team Work")
        st.image("https://raw.githubusercontent.com/CertSkill/teamwork-cert/main/badge.png", width=300)
    else:
        st.warning("Continua ad allenarti per ottenere la certificazione.")

    if st.button("🔄 Ricomincia il test"):
        st.session_state.clear()
        st.rerun()
