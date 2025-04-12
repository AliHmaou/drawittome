import zlib
import base64
import duckdb as ddb
import ast
import gradio as gr
import io
import requests
from PIL import Image
from doc import getDoc

def duckdb_init_secrets(api_key="", model="qwen-2.5-coder-32b"):
    #ddb.connect("./data/memory.duckdb")
    ddb.execute("INSTALL FLOCKMTL FROM community")
    ddb.execute("LOAD FLOCKMTL")
    try:
        ddb.execute(f"""
                        CREATE SECRET groq (
                            TYPE OPENAI,
                            BASE_URL 'https://api.groq.com/openai/v1/',
                            API_KEY '{api_key}'
                        );  
                        """)
    except:
        print("secret already set")
    ddb.sql("""DELETE MODEL 'mermaid_generator';
            """)
    ddb.execute("""
                    CREATE MODEL(
                        'mermaid_generator',
                        '"""+model+"""',
                        'openai',
                        {"context_window": 128000, "max_output_tokens": 32000}
                    );  
                """)
    return "✅ Configuration réussie! Secret temporaire activé.", model

def duckdb_init_prompt(prompt="", precisions=""):
    if prompt=="":
        prompt="""Génère le code mermaid, et rien que le code dans le champ json "mermaid_code", expliquant le mieux la description qui suit.
                    Fais en sorte que les noms des entités mermaid soient concis.
                    Evite les caractères qui feraient bugger le script mermaid : **évite les parenthèses () si tu veux préciser**
                    Dans le champ mermaid_diag_type tu vas indiquer le type de diagramme selon la pertinence définie ci-après.
                    Voici la liste des types de diagrammes avec un rappel de la pertinence :
                    - Graph TB : choix par défaut, essaie de regrouper par blocs, mets des couleurs ;
                    - flowchart TD : pour les processus et arbres de décisions ;
                    - sequenceDiagram : pour les processus complexes ;
                    - classDiagram : si demande explicite ou entrants techniques comme un schéma sql ;
                    - stateDiagram-v2 : si demande explicite ou entrants techniques comme une user story ;
                    - erDiagram : choix par défaut, essaie de regrouper par blocs, mets des couleurs ;
                    - gantt : si thématique projet ou travaux avec des tâches identifiables ;
                    - timeline : si chronologie, historique, biographie, regroupe par décennie, ou siecle si nécessaire pour limiter à 10 colonnes. (syntaxe : timeline    title History of Social Media Platform    2002 : LinkedIn    2004 : Facebook         : Google    2005 : YouTube    2006 : Twitter)
                Le schéma est dans la langue exprimée par le demandeur ou dans la langue du texte d origine.
                """

    ddb.execute("""DELETE PROMPT 'mermaid_generator_prompt';
                """)
    ddb.execute(f"""CREATE PROMPT('mermaid_generator_prompt', '{prompt}. Précisions utilisateur importantes : {precisions}.')
                """)
    return "✅ Prompt configuré avec succès"


def duckdb_code_from_text(input_text="A car got repaired but hit a tree and got wrecked again."):
    query = """
    with llm_result as (
        select 
        llm_complete_json(
            {'model_name': 'mermaid_generator','secret_name': 'groq' }, 
            {'prompt_name': 'mermaid_generator_prompt', 'version': 1}, 
            {'prompt_input': ?}
        )::json AS json_result
    ) 
    select json_result.mermaid_code, json_result.mermaid_diag_type from llm_result
    """
    res = ddb.execute(query, [input_text]).fetchdf()
    mermaid_code = ast.literal_eval(res["mermaid_code"][0])
    mermaid_type = ast.literal_eval(res["mermaid_diag_type"][0])
    return mermaid_code, mermaid_type


def kroki_img_from_mermaid(mermaid_code: str, output_format: str = "svg") -> str:
    compressed = zlib.compress(mermaid_code.encode('utf-8'))
    b64 = base64.urlsafe_b64encode(compressed).decode('utf-8')
    image_url = f"https://kroki.io/mermaid/{output_format}/{b64}"
    html_img = f"""<a href="{image_url}" target="_blank"> <img src="{image_url}" alt="Diagramme Mermaid via Kroki" > </a>"""
    return html_img


def generate_diagram(text_input, additional_details_input):
    duckdb_init_prompt(precisions=additional_details_input)
    mermaid_code, mermaid_diag_type = duckdb_code_from_text(input_text=text_input)
    kroki_html = kroki_img_from_mermaid(mermaid_code)
    return gr.Markdown(kroki_html), gr.Markdown(value=mermaid_code), f"📊 **Type**: {mermaid_diag_type}", gr.Markdown(value=kroki_html)

css = """
.app-header {
    text-align: center;
    margin-bottom: 10px;
}
.app-title {
    font-size: 2.5em !important;
    font-weight: bold !important;
    margin: 10px 0 !important;
}
.app-subtitle {
    font-size: 1.1em !important;
    margin-bottom: 20px !important;
    color: #555;
}
.footer {
    text-align: center;
    margin-top: 20px;
    color: #666;
    font-size: 0.9em;
}
"""

with gr.Blocks(css=css, theme="soft") as demo:
    gr.HTML("""
        <div class="app-header">
            <h1 class="app-title">🎨 DrawItToMe</h1>
            <p class="app-subtitle">Parcequ'un schéma vaut mieux qu'un long discours.</p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            text_input = gr.Textbox(
                label="📝 Description du diagramme", 
                placeholder="Décrivez le diagramme que vous souhaitez générer... Par exemple : 'Un processus d'achat en ligne avec panier, paiement et livraison'",
                lines=15
            )
            additional_details_input = gr.Textbox(
                label="🔍 Précisions supplémentaires", 
                placeholder="Précisez le type de diagramme souhaité ou ajoutez des détails (optionnel)"
            )
            
            with gr.Row():
                generate_button = gr.Button("✨ Générer le diagramme", variant="primary")
                clear_button = gr.Button("🗑️ Effacer", variant="secondary")
            
        with gr.Column(scale=4):
            with gr.Tab(label="📊 Diagramme"):
                image_output = gr.Markdown(
                    label="Visualisation", 
                    container=True, 
                    min_height=400, 
                    show_copy_button=True, 
                    show_label=True
                )
                gr.HTML("<p><i>Cliquez sur l'image pour l'ouvrir en plein écran</i></p>")
                
            with gr.Tab(label="💻 Code"):
                mermaid_code = gr.Code(
                    label="Code Mermaid généré", 
                    language="markdown"
                )
                mermaid_diag_type = gr.Markdown(
                    label="Type de diagramme",
                    container=True
                )
                mermaid_link = gr.Markdown(
                    label="Lien direct",
                    container=True
                )
                
            with gr.Tab(label="⚙️ Configuration"):
                gr.HTML("<h3>Configuration de l'API</h3>")
                groq_secret = gr.Text(
                    label="🔑 Clé API Groq", 
                    placeholder="Entrez votre clé API Groq"
                )
                gr.HTML("<p><i>Obtenez une clé gratuite sur <a href='https://groq.com/' target='_blank'>groq.com</a></i></p>")
                
                groq_model = gr.Text(
                    label="🤖 Modèle Groq", 
                    value="qwen-qwq-32b",
                    placeholder="Nom du modèle à utiliser"
                )
                gr.HTML("<p><i>Consultez les modèles disponibles sur <a href='https://console.groq.com/docs/models' target='_blank'>console.groq.com/docs/models</a></i></p>")
                
                groq_secret_button = gr.Button("💾 Enregistrer la configuration", variant="primary")
            with gr.Tab(label="✍🏽 Coder's notes"):
                gr.Markdown(value=getDoc())
    with gr.Row():
        with gr.Column():
            gr.HTML("<h3>Exemples de descriptions pour vous inspirer</h3>")
            gr.Examples(
                examples=[
                    ["Une voiture a un moteur et 4 roues", 
                    "Diagramme de classe"],
                    ["Lorsqu'un service public régulier ou à la demande de transport routier est situé pour la plus grande partie de son parcours en Ile-de-France, et avec l'accord préalable des autorités organisatrices intéressées par la partie du service extérieure à la région, le syndicat peut inscrire l'ensemble du service au plan régional de transport.", 
                    "Diagramme de séquence"],
                    [""" Le projet date de 1989, année où le gouvernement de Michel Rocard cherche à résoudre le problème de la saturation de la ligne A du RER. La SNCF présentera le projet EOLE (la ligne E du RER) et la RATP le projet Meteor (ligne 14). Le projet initial devait relier la Porte Maillot à l'ouest à la Porte d'Ivry à l'est. Finalement le projet est pour des raisons de coût limité à l'ouest à Saint-Lazare et à l'est à Bibliothèque François-Mitterrand. Un atelier souterrain est prévu pour être transformé plus tard en station. Dans un premier temps la ligne est limitée à Madeleine.
    Un MP14
    Les travaux débutent alors à la fin de 1989 et le tunnel commence à être creusé en 1993. Le tronçon entre gare de Lyon et Cour Saint Emillion est édifié à ciel ouvert afin de réduire les coups de construction. Le passage sous la seine est construit grâce à la traditionnelle méthode des caissons immergés.
    La ligne est inaugurée en octobre 1998 et relie la station Madeleine (8ème arrondissement) à la station Bibliothèque François-Mitterrand dans le 13ème. En 2003, la ligne est prolongée de Madeleine à la gare Saint-Lazare. Elle est prolongée de la Bibliothèque aux Olympiades en 2007 en réutilisant l'atelier souterrain un autre atelier étant construit plus loin.
    La fréquentation de la ligne de cesse de croître. Elle fait dorénavant partie du projet du Grand Paris Express, La ligne est donc prolongée en juin 2024 de Saint-Ouen à Saint-Denis au nord et de Olympiades à l'aéroport d'Orly au sud.
    Le 12 octobre 2020, la ligne 14 a reçu les nouvelles rames de métro pneumatique : le MP14 aux couleurs d'Île-de-France Mobilités. Ces nouvelles rames comptent 8 voitures contre 6 pour les anciens MP89 CA et MP05. Cette augmentation de la taille des rames est due à l'augmentation brutale du trafic attendue en raison du prolongement à l'aéroport d'Orly.""", 
                    "Diagramme de Gantt"],
                    ["""Historique
    Comité des transports parisiens
    Île-de-France Mobilités est l'héritière de plusieurs formes d'organisations chargées des transports parisiens depuis les années 1930. En 1938, un décret-loi crée le Comité des transports parisiens, avec une majorité de représentants de l'État. Cet organisme avait pour mission de coordonner les transports collectifs en région parisienne.
    Office régional des transports parisiens
    En 1948, une réorganisation crée la Régie autonome des transports parisiens (RATP) et l'Office régional des transports parisiens (ORTP), qui remplace le Comité. Le décret du 14 novembre 1949 établit les bases de l'organisation des transports toujours en vigueur : l'État finance le déficit de la SNCF, tandis que les collectivités locales subventionnent la RATP.
    Syndicat des transports parisiens (STP)
    En 1959, l'ORTP devient le Syndicat des transports parisiens (STP), un établissement public regroupant l'État, la mairie de Paris et plusieurs départements. Son rôle est de moderniser les transports en commun et de coordonner l'ensemble des acteurs : la RATP, la SNCF et de nombreuses entreprises privées. Le STP supervise les investissements, les projets d'aménagement et les actions pour améliorer la qualité de service.""", 
                    "Timeline"],
                    ["Processus d'inscription à un service en ligne : l'utilisateur s'inscrit, reçoit un email de confirmation, active son compte, configure son profil et peut ensuite utiliser le service", 
                    "Organigramme (flowchart)"]
                ],
                inputs=[text_input, additional_details_input],
                label="Exemples prêts à l'emploi"
            )

            
    
    gr.HTML("""
        <div class="footer">
            <p>DrawItToMe utilise <a href="https://kroki.io" target="_blank">Kroki.io</a> pour le rendu des diagrammes Mermaid | 
            Propulsé par Groq et DuckDB/FlockMTL</p>
        </div>
    """)
    
    # Event handlers
    additional_details_input.submit(
        fn=generate_diagram,
        inputs=[text_input, additional_details_input],
        outputs=[image_output, mermaid_code, mermaid_diag_type, mermaid_link]
    )
    
    text_input.submit(
        fn=generate_diagram,
        inputs=[text_input, additional_details_input],
        outputs=[image_output, mermaid_code, mermaid_diag_type, mermaid_link]
    )
    
    generate_button.click(
        fn=generate_diagram,
        inputs=[text_input, additional_details_input],
        outputs=[image_output, mermaid_code, mermaid_diag_type, mermaid_link]
    )
    
    clear_button.click(
        fn=lambda: ("", ""),
        inputs=[],
        outputs=[text_input, additional_details_input]
    )
    
    groq_secret_button.click(
        fn=duckdb_init_secrets,
        inputs=[groq_secret, groq_model],
        outputs=[groq_secret, groq_model]
    )

# Launch the interface
if __name__ == "__main__":
    demo.launch(show_error=True)