import streamlit as st
import openai

st.set_page_config(page_title="Certificazione Team Work", layout="centered")

# Inizializzazione variabili di sessione
if "step" not in st.session_state:
    st.session_state.step = "profilo"
    st.session_state.profilo_utente = {}
    st.session_state.domande = []
    st.session_state.indice = 0
    st.session_state.risposte = []
    st.session_state.punteggi = []
    st.session_state.valutazioni = []

# --- Funzioni ---

def genera_prompt_iniziale(profilo):
    return f"""Sei un esperto psicologo del lavoro. In base al seguente profilo:
Nome: {profilo['nome']}, Età: {profilo['eta']}, Azienda: {profilo['azienda']}, Settore: {profilo['settore']}, Ruolo: {profilo['ruolo']}, Esperienza settore: {profilo['anni_settore']} anni, Esperienza ruolo: {profilo['anni_ruolo']} anni
Genera una domanda per valutare il teamwork composta da:
- Scenario di contesto
- Problema osservato
- Domanda specifica
Scrivi ogni parte su una riga diversa senza numerarle."""

def genera_domanda_dinamica(profilo, storia_risposte):
    contesto = "\n".join([f"D: {d}\nR: {r}" for d, r in storia_risposte])
    return f"""Profilo:
Nome: {profilo['nome']}, Età: {profilo['eta']}, Azienda: {profilo['azienda']}, Settore: {profilo['settore']}, Ruolo: {profilo['ruolo']}, Esperienza settore: {profilo['anni_settore']} anni, Esperienza ruolo: {profilo['anni_ruolo']} anni

Storia risposte:
{contesto}

Genera una nuova domanda per continuare il test sul teamwork. Domanda situazionale, breve, senza spiegazioni, strutturata in:
- Scenario di contesto
- Problema
- Domanda
Ogni parte su una riga diversa."""

def valuta_risposta(risposta):
    prompt = f"""Valuta questa risposta in un contesto di lavoro in team:
\"{risposta}\"
Assegna un punteggio da 0 a 100 per:
- Collaborazione
- Comunicazione
- Leadership
- Problem solving
- Empatia
Spiega brevemente ogni punteggio."""
    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

def genera_descrizione_finale(profilo, media):
    descrizione_prompt = f"""Genera una descrizione di 15 righe del profilo comportamentale di un candidato chiamato {profilo['nome']}.
Età: {profilo['eta']}, Azienda: {profilo['azienda']}, Settore: {profilo['settore']}, Ruolo: {profilo['ruolo']}, Esperienza: {profilo['anni_settore']} anni nel settore, {profilo['anni_ruolo']} anni nel ruolo.
Punteggi:
Collaborazione: {media['Collaborazione']}
Comunicazione: {media['Comunicazione']}
Leadership: {media['Leadership']}
Problem solving: {media['Problem solving']}
Empatia: {media['Empatia']}
Scrivi una valutazione complessiva, evidenzia punti di forza e debolezza, e suggerisci 3 corsi formativi adatti senza specificare scuole o link."""
    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": descrizione_prompt}]
    )
    return res.choices[0].message.content.strip()

# --- Fase 1: Profilazione ---
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
                "nome": nome, "eta": eta, "azienda": azienda, "settore": settore,
                "ruolo": ruolo, "anni_settore": anni_settore, "anni_ruolo": anni_ruolo
            }
            prompt = genera_prompt_iniziale(st.session_state.profilo_utente)
            domanda = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content.strip()
            st.session_state.domande = [domanda]
            st.session_state.step = "test"
            st.rerun()
        else:
            st.error("Compila tutti i campi prima di iniziare il test.")

# --- Fase 2: Test ---
elif st.session_state.step == "test":
    st.title("Domande dinamiche di Team Work")
    indice = st.session_state.indice

    if "domande" not in st.session_state or len(st.session_state.domande) <= indice:
        st.error("Errore: domanda non trovata.")
        st.stop()

    domanda = st.session_state.domande[indice].splitlines()
    st.markdown(f"**Domanda {indice + 1} di 30**")
    for line in domanda:
        st.markdown(f"{line}")

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

        if st.session_state.indice < 30:
            nuova = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": genera_domanda_dinamica(
                    st.session_state.profilo_utente,
                    list(zip(st.session_state.domande, st.session_state.risposte))
                )}]
            ).choices[0].message.content.strip()
            st.session_state.domande.append(nuova)
        else:
            st.session_state.step = "risultato"

        st.rerun()

# --- Fase 3: Risultato ---
elif st.session_state.step == "risultato":
    st.title("✅ Profilazione completata")

    media = {}
    for k in ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]:
        valori = [p.get(k, 0) for p in st.session_state.punteggi if k in p]
        media[k] = round(sum(valori)/len(valori), 2)

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

    st.markdown("### 📃 Descrizione del profilo")
    descrizione = genera_descrizione_finale(st.session_state.profilo_utente, media)
    for riga in descrizione.split("\n"):
        st.markdown(riga)

    if st.button("🔄 Ricomincia il test"):
        st.session_state.clear()
        st.rerun()
