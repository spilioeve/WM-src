# World Modelers Project

# SOFIA: Semantic Open-Field Information Analyzer 

This repo contains source code and other necessary files (eg Ontology) to run SOFIA tool. The input can be a sentence or a set of files which are already preprocessed via Stanford CoreNLP and stored as json. The output will be an xsl file containing all the relations that SOFIA identified.

# Below is a short description of SOFIA system and an explanation/rationale behind the output:

SOFIA is an Information Extraction system that currently detects Causal Relationships explicitly mentioned in the same sentence. SOFIA is built based upon prominent Linguistic Theories that view Causality as a discourse relation between two Eventualities. Following this approach, SOFIA extracts three major classes of information: Entities, Events and Relations. All those classes are important in order to build a coherent model that captures the semantics of a sentence. Entities include the physical objects, people, organizations, etc, while eventualities denote some action/event, process, change of state that happens. Entities are arguments in Events (eg The car moves), while Events are arguments in Relations like Causality. In some cases, events can also be arguments for other events, which is a current area of research for SOFIA's modeling. Such events include 'increase/decrease' types amongst others, which in some cases might imply Causality (eg Drought increases famine), but in many others they do not (eg Drought increased over the last year). Thus, we consider important to carefully think how to model those before returning them as part of SOFIA's output.

SOFIA currently grounds the detected Events and Entities to her internal Ontology, We note that although the Ontology is subject to change in the future, we do not plan to change the Upper Level structure. Additional Information includes Time and Location, which SOFIA extracts for Events, when possible.
