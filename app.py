import zlib
import base64
import duckdb as ddb
import ast
import gradio as gr
import io
import requests
from PIL import Image

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
    return "Duckdb/FlockMTL ready, temporary secret will be destroyed after session.", model

def duckdb_init_prompt(prompt="", precisions=""):
    if prompt=="":
        prompt='Génère le code mermaid, et rien que le code dans le champ json "mermaid_code", expliquant le mieux la description qui suit, et avec un effort d originalité. Fais en sorte que les noms des entités mermaid soient concis et évite les caractères qui feraient bugger le script mermaid, les parenthèses font partie de la syntaxe réservée. Dans le champ mermaid_diag_type tu vas indiquer le type de diagramme le plus adapté que tu as choisi ou que l utilisateur t a demandé.'

    ddb.execute("""DELETE PROMPT 'mermaid_generator_prompt';
                """)
    ddb.execute(f"""CREATE PROMPT('mermaid_generator_prompt', '{prompt}. Précisions utilisateur importantes : {precisions}.')
                """)
    return "FlockMTL prompt set"


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
    html_img = f"""<a href="{image_url}"> <img src="{image_url}" alt="Diagramme Mermaid via Kroki"> </a>"""
    return html_img


def generate_diagram(text_input, additional_details_input):
    duckdb_init_prompt(precisions=additional_details_input)
    mermaid_code, mermaid_diag_type = duckdb_code_from_text(input_text=text_input)
    kroki_html=kroki_img_from_mermaid(mermaid_code)
    return gr.Markdown(kroki_html),gr.Markdown(value=mermaid_code), mermaid_diag_type, gr.Markdown(value=kroki_html)

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Accordion(label="Set API Key & Model",open=False):
                groq_secret = gr.Text(label="Groq Key, get yours for free here : https://groq.com/", value="KEY") # non sensitive key
                groq_model = gr.Text(label="Groq model, see : https://console.groq.com/docs/models", value="qwen-qwq-32b")
                groq_secret_button = gr.Button("Store secret and model")
            text_input = gr.Textbox(label="Text to Generate Diagram", lines=20)
            additional_details_input = gr.Textbox(label="Additional Details")
            generate_button = gr.Button("Generate Diagram")
            
        with gr.Column(scale=4):
            with gr.Tab(label="Diagram"):
                image_output = gr.Markdown(label="Generated Diagram", container=True, min_height=400, show_copy_button=True, show_label=True)
            with gr.Tab(label="Code"):
                mermaid_code = gr.Code(label="Generated code", language="markdown")
                mermaid_diag_type = gr.Markdown(label="Type de diagramme",container=True)
                mermaid_link = gr.Markdown(label="Visualisation",container=True)
            
    with gr.Row():
        gr.Examples(
                examples=[
                    ["Une voiture a un moteur et 4 roues", 
                     ""],
                    ["Lorsqu'un service public régulier ou à la demande de transport routier est situé pour la plus grande partie de son parcours en Ile-de-France, et avec l'accord préalable des autorités organisatrices intéressées par la partie du service extérieure à la région, le syndicat peut inscrire l'ensemble du service au plan régional de transport.", 
                     "Diagramme de séquence, "],
                    [""" Le projet date de 1989, année où le gouvernement de Michel Rocard cherche à résoudre le problème de la saturation de la ligne A du RER. La SNCF présentera le projet EOLE (la ligne E du RER) et la RATP le projet Meteor (ligne 14). Le projet initial devait relier la Porte Maillot à l'ouest à la Porte d'Ivry à l'est. Finalement le projet est pour des raisons de coût limité à l'ouest à Saint-Lazare et à l'est à Bibliothèque François-Mitterrand. Un atelier souterrain est prévu pour être transformé plus tard en station. Dans un premier temps la ligne est limitée à Madeleine.
Un MP14
Les travaux débutent alors à la fin de 1989 et le tunnel commence à être creusé en 1993. Le tronçon entre gare de Lyon et Cour Saint Emillion est édifié à ciel ouvert afin de réduire les coups de construction. Le passage sous la seine est construit grâce à la traditionnelle méthode des caissons immergés.
La ligne est inaugurée en octobre 1998 et relie la station Madeleine (8ème arrondissement) à la station Bibliothèque François-Mitterrand dans le 13ème. En 2003, la ligne est prolongée de Madeleine à la gare Saint-Lazare. Elle est prolongée de la Bibliothèque aux Olympiades en 2007 en réutilisant l'atelier souterrain un autre atelier étant construit plus loin.
La fréquentation de la ligne de cesse de croître. Elle fait dorénavant partie du projet du Grand Paris Express, La ligne est donc prolongée en juin 2024 de Saint-Ouen à Saint-Denis au nord et de Olympiades à l'aéroport d'Orly au sud.
Le 12 octobre 2020, la ligne 14 a reçu les nouvelles rames de métro pneumatique : le MP14 aux couleurs d'Île-de-France Mobilités. Ces nouvelles rames comptent 8 voitures contre 6 pour les anciens MP89 CA et MP05. Cette augmentation de la taille des rames est due à l'augmentation brutale du trafic attendue en raison du prolongement à l'aéroport d'Orly.""", 
                     "Diagramme de Gantt, attention syntaxe (A task :a1, 2014-01-01, 30d)"],
                    ["""Historique
Comité des transports parisiens
Île-de-France Mobilités est l’héritière de plusieurs formes d’organisations chargées des transports parisiens depuis les années 1930. En 1938, un décret-loi crée le Comité des transports parisiens, avec une majorité de représentants de l’État. Cet organisme avait pour mission de coordonner les transports collectifs en région parisienne.
Office régional des transports parisiens
En 1948, une réorganisation crée la Régie autonome des transports parisiens (RATP) et l’Office régional des transports parisiens (ORTP), qui remplace le Comité. Le décret du 14 novembre 1949 établit les bases de l’organisation des transports toujours en vigueur : l’État finance le déficit de la SNCF, tandis que les collectivités locales subventionnent la RATP.
Syndicat des transports parisiens (STP)
En 1959, l’ORTP devient le Syndicat des transports parisiens (STP), un établissement public regroupant l’État, la mairie de Paris et plusieurs départements. Son rôle est de moderniser les transports en commun et de coordonner l’ensemble des acteurs : la RATP, la SNCF et de nombreuses entreprises privées. Le STP supervise les investissements, les projets d’aménagement et les actions pour améliorer la qualité de service.
À partir de 1968, le STP intègre les nouveaux départements franciliens. En 1971, il se voit confier la gestion du versement transport, une taxe sur les salaires destinée à financer les transports. En 1975, il met en place la carte orange, premier titre de transport valable sur l’ensemble du réseau.
En 1991, la compétence du STP s’élargit à toute la région Île-de-France.
Le STIF dans les années 2000
En 2000, un nouveau système de financement par contrats pluriannuels est mis en place pour responsabiliser les opérateurs de transport. La loi SRU transforme le STP en Syndicat des transports d’Île-de-France (STIF), un établissement public placé sous la tutelle de la région, marquant un retrait progressif de l’État.
L’évolution se poursuit jusqu’en 2006 avec un conseil d’administration désormais présidé par le président du conseil régional. Le STIF gagne en compétences, notamment pour les infrastructures, les transports scolaires et fluviaux.
Cependant, plusieurs décisions de l’État viennent limiter ces compétences, comme le retrait du projet du Grand Paris ou le transfert d’infrastructures à la RATP.
Le contrat 2012–2015 est signé après négociation avec la SNCF. Le STIF prend en charge certaines charges sociales, tandis que la SNCF accepte un système de bonus-malus basé sur la ponctualité. En 2012, un vaste plan d'amélioration du réseau est lancé, incluant de nouveaux bus, la modernisation du RER A et des lignes fluviales.
Le Nouveau Grand Paris
Lancé en 2013, ce projet combine le Grand Paris Express (piloté par la Société du Grand Paris) et le plan de mobilisation pour les transports coordonné par le STIF. En 2015, un contrat 2016–2020 est signé entre le STIF, la RATP et la SNCF, avec plus de 20 milliards d’euros d’investissement pour moderniser le réseau et améliorer l’offre de transport.
De STIF à Île-de-France Mobilités
Le 26 juin 2017, le STIF change de nom pour devenir Île-de-France Mobilités. Cette nouvelle identité est officialisée par la loi en 2019.
En 2021, une feuille de route sur cinq ans est adoptée, visant à simplifier la grille tarifaire, renforcer la lutte contre les incivilités, augmenter l’offre de bus et développer le service Véligo (vélos à assistance électrique).
En 2022, l’établissement fait face à de fortes difficultés financières, avec une dette atteignant près de neuf milliards d’euros.""", 
                     """Timeline, en regroupant par décennie, exemple pour la syntaxe : 
                     timeline 
                        title History of Social Media Platform
                        2002 : LinkedIn
                        2004 : Facebook
                             : Google
                        2005 : YouTube
                        2006 : Twitter """],
                     ["Elon Reeve Musk naît le 28 juin 1971 à Pretoria, dans la province du Transvaal, en Afrique du Sud. Au moment de sa naissance, le pays est sous le régime de l'apartheid, instauré en 1948 par le Parti national, qui exerce un pouvoir raciste et répressif[2],[3]. Il est le fils d'Errol Musk, riche ingénieur et promoteur immobilier sud-africain aux origines afrikaner (néerlandaise), Pennsylvania Dutch (allemande)[4] et anglo-sud-africaine, ayant eu des parts (contrairement aux affirmations du milliardaire) d'une mine d'émeraudes en Zambie[5],[6],[7], et de Maye Haldeman, une diététicienne et mannequin canadienne et sud-africaine[8],[9],[10],[11],[12]. Une arrière-grand-mère paternelle d'Elon descend de Free Burghers (en) (Bourgeois Libres) hollandais, tandis que des arrière-grands-parents maternels sont des Pennsylvania Dutch venant d'un village de Suisse alémanique, du côté de la famille Haldeman (en), dont le nom évoque ces racines[13]. La famille de sa mère, qui est née en Saskatchewan, quitte le Canada pour Pretoria en Afrique du Sud en 1950 et obtient la double nationalité[14]. Le grand-père maternel d'Elon, Joshua Norman Haldeman, né canadien aux États-Unis, homme politique, pionnier de la chiropratique au Canada et détenteur de records en tant qu'aviateur grâce à des voyages en famille en Afrique et en Australie, meurt en 1974, alors qu'Elon est encore un enfant en bas âge[4].", 
                     "Organigramme"]
                ],
                inputs=[text_input, additional_details_input],
                label="Exemples"
            )
    additional_details_input.submit(
        fn=generate_diagram,
        inputs=[text_input, additional_details_input],
        outputs=[image_output, mermaid_code,mermaid_diag_type,mermaid_link]
    )
    text_input.submit(
        fn=generate_diagram,
        inputs=[text_input, additional_details_input],
        outputs=[image_output, mermaid_code,mermaid_diag_type,mermaid_link]
    )
    generate_button.click(
        fn=generate_diagram,
        inputs=[text_input, additional_details_input],
        outputs=[image_output, mermaid_code,mermaid_diag_type,mermaid_link]
    )
    groq_secret_button.click(
        fn=duckdb_init_secrets,
        inputs=[groq_secret,groq_model],
        outputs=[groq_secret, groq_model]
    )

# Launch the interface
if __name__ == "__main__":
    demo.launch(show_error=True)