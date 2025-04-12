import gradio as gr

def getDoc():
    return """# DrawItToMe : transformer du texte en diagrammes Mermaid

    ## Présentation

    **DrawItToMe** est une application web qui convertit des descriptions textuelles en diagrammes Mermaid, grâce à une combinaison de technologies open-source et de modèles de langage performants. L’application propose une interface simple pour générer automatiquement des visualisations compréhensibles à partir de texte libre.

    ---

    ## Architecture générale

    L’application repose sur quatre composants principaux :

    [![Aperçu du pipeline](https://kroki.io/mermaid/svg/eNpNjkFOwzAURPecYi5QkGBfKYmhCiTQkohN1IWVfForjR1-vgsLX6jn6MWwzIZZjvTezIH1fESrbhCTdaUV4k_dE7yYk1m0kGdsWA_G7bFarcOjFb5eCEI_QgF517I2QhNZgfL9qPK7p5Prx7qt9kmaJ2zLbpoFi7DvxUdDQNFl2zK63Reqqsbumywe7vM_qkjU-_UyO7sQnpu31zj2T1i4gVATT9oMAapriM8m_o4tkx08XtiN5jbeTpBKUDnpA6H52ARkvxuPUUw=)](https://kroki.io/mermaid/svg/eNpNjkFOwzAURPecYi5QkGBfKYmhCiTQkohN1IWVfForjR1-vgsLX6jn6MWwzIZZjvTezIH1fESrbhCTdaUV4k_dE7yYk1m0kGdsWA_G7bFarcOjFb5eCEI_QgF517I2QhNZgfL9qPK7p5Prx7qt9kmaJ2zLbpoFi7DvxUdDQNFl2zK63Reqqsbumywe7vM_qkjU-_UyO7sQnpu31zj2T1i4gVATT9oMAapriM8m_o4tkx08XtiN5jbeTpBKUDnpA6H52ARkvxuPUUw=)

    1. **Interface utilisateur (Gradio)**  
    Une interface légère développée en Python avec Gradio, structurée autour de champs de saisie textuelle, d'onglets, et de retours visuels immédiats.

    2. **Orchestration (DuckDB + FlockMTL)**  
    L’application utilise DuckDB enrichi de l’extension FlockMTL pour :
    - la gestion sécurisée des secrets d’API,
    - la structuration et le versionnage des prompts envoyés au modèle,
    - le traitement des retours JSON.

    3. **Modèle de génération (Qwen 32B via Groq)**  
    Le texte est envoyé à un modèle LLM déployé sur l’infrastructure Groq. Ce modèle retourne un code Mermaid structuré, ainsi que le type de diagramme le plus adapté.

    4. **Rendu graphique (Kroki.io)**  
    Le code Mermaid est encodé et compressé dans une URL, puis envoyé à Kroki.io pour générer une image SVG, affichée directement dans l’application.

    ---

    ## Défis techniques

    ### 1. Fiabilité des réponses JSON

    Les LLM génèrent parfois des structures JSON incorrectes.  
    **Solution** : Utilisation de FlockMTL pour forcer un format strict, avec validation automatique des champs `mermaid_code` et `mermaid_diag_type`.

    ### 2. Rendu sans backend

    L’objectif était d’éviter une API de rendu côté serveur.  
    **Solution** : Encodage du code Mermaid dans l’URL, compressé avec zlib, puis envoyé à Kroki en lecture seule. Cela élimine le besoin d'une infrastructure dédiée.

    ### 3. Choix du modèle LLM

    Plusieurs modèles ont été testés.  
    **Conclusion** : Qwen 32B offre un bon compromis entre performance, latence et consommation. Il est capable de générer des structures Mermaid syntaxiquement valides avec un coût modéré.

    ---

    ## Sécurité

    - Les clés API ne sont jamais persistées, uniquement stockées temporairement en mémoire.
    - Aucune donnée utilisateur n’est enregistrée.
    - Kroki.io est utilisé comme service de rendu externe, limitant les risques liés au traitement local.

    ---

    ## Perspectives

    L’architecture de DrawItToMe permet d’envisager des évolutions :
    - Support d’autres formats de diagrammes (PlantUML, GraphViz),
    - Édition visuelle du code Mermaid,
    - Collaboration en temps réel,
    - Thématisation des diagrammes.

    ---

    ## Conclusion

    DrawItToMe démontre qu’il est possible de bâtir une application utile et modulaire en s’appuyant sur des composants open-source spécialisés. La combinaison DuckDB + FlockMTL + Groq + Kroki permet de transformer du texte libre en visualisation structurée de manière fiable, sans compromis sur l’ergonomie ou la robustesse.

    ---

    """