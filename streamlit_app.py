import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import graphviz
from annotated_text import annotated_text

# Load API_KEY
load_dotenv()
openai_api_key = os.getenv("API_KEY")

# Read JSON file containing the prompts
prompts_agents = []
prompts_consensus = []
json_file_path = "./prompts.json"
try:
    with open(json_file_path, "r") as json_file:
        prompts = json.load(json_file)
        prompts_agents = prompts["agents"]
        prompts_consensus = prompts["consensus"]
except:
    st.write("Erreur lors du chargement du fichier contenant les prompts.")

# Tabs
tab1, tab2 = st.tabs(["Résumeur", "Extracteur"])

with tab1:
    # Show title and description
    st.title("Résumeur de rapport")
    st.write("Application de synthèse de rapport de défense par IA générative. Ce système utilise quatre agents basé sur le LLM `GPT-3.5`. Il effectue trois analyses indépendantes puis réalise un consensus entre les trois versions obtenues. Vous pouvez paramétrer le système avec différentes versions de *prompts* pour chaque agent.")

    # Create a graphlib graph object
    graph = graphviz.Digraph()
    graph.attr(rankdir='LR')
    graph.attr('node', shape='plaintext')
    graph.node("Rapport (entrée)")
    graph.attr('node', shape='circle')
    graph.edge("Rapport (entrée)", "Agent\nAnalyseur 1")
    graph.edge("Rapport (entrée)", "Agent\nAnalyseur 2")
    graph.edge("Rapport (entrée)", "Agent\nAnalyseur 3")
    graph.edge("Agent\nAnalyseur 1", "Agent\nConsensus")
    graph.edge("Agent\nAnalyseur 2", "Agent\nConsensus")
    graph.edge("Agent\nAnalyseur 3", "Agent\nConsensus")
    graph.attr('node', shape='plaintext')
    graph.edge("Agent\nConsensus", "Résumé (sortie)")
    st.graphviz_chart(graph)

    # Create an OpenAI client
    client = OpenAI(api_key=openai_api_key)

    # Split into three columns for three selects
    cols = st.columns(3)
    selected_prompts_agents = [None, None, None]

    # Option to select the prompt for each agent
    for i in range(3):
        with cols[i]:
            option = st.selectbox(
                "Agent Analyseur " + str(i + 1),
                (p["name"] for p in prompts_agents),
            )
            for prompt_agent in prompts_agents:
                if prompt_agent["name"] == option:
                    selected_prompts_agents[i] = prompt_agent["prompt"]
                    break

    # Option to select the prompt for consensus agent
    selected_prompt_consensus = None
    option = st.selectbox(
        "Agent Consensus",
        (p["name"] for p in prompts_consensus),
    )
    for prompt_consensus in prompts_consensus:
        if prompt_consensus["name"] == option:
            selected_prompt_consensus = prompt_consensus["prompt"]
            break

    # Create a drag and drop zone for loading report files
    uploaded_file = st.file_uploader("Sélectionnez un rapport à analyser", key=1, type="TXT")

    # Read and store the content of the file into a string variable
    if uploaded_file is not None and st.button("C'est parti !"):
        report_content = uploaded_file.read().decode("utf-8")

        # Display the report content as the user's message
        with st.chat_message("user"):
            st.markdown(report_content)

        # Generate responses for each analyzer agents using the OpenAI API
        results_agents = [None, None, None]
        for i in range(3):
            results_agents[i] = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": selected_prompts_agents[i] + "\n\n" + report_content}],
                stream=True,
            )
        
        # Display responses and store their actual result contents
        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                with st.chat_message("assistant", avatar=f":material/counter_{i + 1}:"):
                    results_agents[i] = st.write_stream(results_agents[i])
        
        # Concatenate all results into one string variable
        all_results_agents = ""
        for i in range(3):
            all_results_agents += f"\n\nRésumé {i + 1} :\n" + results_agents[i]
        
        # Generate response for the consensus agent using the OpenAI API
        results_consensus = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": selected_prompt_consensus + all_results_agents}],
            stream=True,
        )

        # Stream the response to the chat using `st.write_stream`
        with st.chat_message("assistant"):
            results_consensus = st.write_stream(results_consensus)
        
        # Button to download the text file
        st.download_button(
            label="Télécharger le résumé",
            data=results_consensus,
            file_name="resume_rapport.txt",
            mime="text/plain",
        )

with tab2:
    # Show title and description
    st.title("Extracteur d'événements et d'attributs")
    st.write("Application d'extraction d'événements et d'attributs dans un rapport de défense par IA générative. Vous pouvez paramétrer le système avec différentes versions de *prompts*.")
    
    # Create a drag and drop zone for loading report files
    uploaded_file = st.file_uploader("Sélectionnez un résumé à traiter", key=2, type="TXT")

    # Read and store the content of the file into a string variable
    if uploaded_file is not None and st.button("C'est parti !"):
        report_content = uploaded_file.read().decode("utf-8")

        # Display the report content as the user's message
        with st.chat_message("user"):
            st.markdown(report_content)

        # TODO: Process the extraction using GPT-3.5
        extracted_mock = [
            (
                "Espionnage militaire",
                "Quoi"
            ),
            (
                "Chiaotou, Kaohisung",
                "Où"
            ),
            (
                "03-01-2024",
                "Quand"
            ),
            (
                "militaires taïwanais",
                "Qui"
            ),
        ]

        # Fonction pour annoter le texte avec les phrases et les étiquettes
        def annotate_text(text, annotations):
            annotated_blocks = []
            last_idx = 0

            # Trier les annotations par ordre d'apparition dans le texte pour éviter les chevauchements
            sorted_annotations = sorted(annotations, key=lambda x: text.find(x[0]))

            for phrase, label in sorted_annotations:
                start_idx = text.find(phrase, last_idx)
                if start_idx != -1:
                    # Ajouter le texte non annoté avant la phrase
                    if start_idx > last_idx:
                        annotated_blocks.append(text[last_idx:start_idx])
                    
                    # Ajouter la phrase annotée
                    annotated_blocks.append((phrase, label))

                    # Mettre à jour l'index de fin de la phrase annotée
                    last_idx = start_idx + len(phrase)

            # Ajouter le reste du texte non annoté
            annotated_blocks.append(text[last_idx:])
            return annotated_blocks

        # Annoter et afficher le texte original
        with st.chat_message("assistant"):
            annotated_text_blocks = annotate_text(report_content, extracted_mock)
            annotated_text(*annotated_text_blocks)
