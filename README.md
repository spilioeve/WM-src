# World Modelers Project

# SOFIA: Semantic Open-Field Information Analyzer 

This repo contains source code and other necessary files (eg Ontology) to run SOFIA tool. The input can be a sentence or a set of files which are already preprocessed via Stanford CoreNLP and stored as json. The output will be an xsl file containing all the relations that SOFIA identified.

# Below is a short description of SOFIA system and an explanation/rationale behind the output:

SOFIA is an Information Extraction system that currently detects Causal Relationships explicitly mentioned in the same sentence. SOFIA is built based upon prominent Linguistic Theories that view Causality as a discourse relation between two Eventualities. Following this approach, SOFIA extracts three major classes of information: Entities, Events and Relations. All those classes are important in order to build a coherent model that captures the semantics of a sentence. Entities include the physical objects, people, organizations, etc, while eventualities denote some action/event, process, change of state that happens. Entities are arguments in Events (eg The car moves), while Events are arguments in Relations like Causality. In some cases, events can also be arguments for other events, which is a current area of research for SOFIA's modeling. Such events include 'increase/decrease' types amongst others, which in some cases might imply Causality (eg Drought increases famine), but in many others they do not (eg Drought increased over the last year). Thus, we consider important to carefully think how to model those before returning them as part of SOFIA's output.

SOFIA currently grounds the detected Events and Entities to her internal Ontology, We note that although the Ontology is subject to change in the future, we do not plan to change the Upper Level structure. Additional Information includes Time and Location, which SOFIA extracts for Events, when possible.

# Usage
First, install the requirements in `requirements.txt`. Note that the [official Python Interface to Stanford CoreNLP](https://github.com/stanfordnlp/python-stanford-corenlp) is not kept up to date on PyPi so it must be installed with:

```
git clone https://github.com/stanfordnlp/python-stanford-corenlp.git
cd python-stanford-corenlp
python setup.py install
```

Next, navigate to this SOFIA directory. Try:

```
from main import SOFIA
sofia = SOFIA(CoreNLP='/Users/brandon/stanford-corenlp-full-2018-10-05')
sentence = '''The intense rain caused flooding in the area and in the capital. This was terrible news for the people of Pandonia. Conflict in the region is on the rise due to the floods. The floods are a direct result of rain and inadequate drainage.'''
results = sofia.getOutputOnline(sentence)
sofia.results2excel('output.xlsx',results)
```

In this example, the `SOFIA` class is invoked to create the object `sofia`. To initialize the `SOFIA` class we must pass it the path to our unzipped CoreNLP installation. `SOFIA` uses the Python interface to CoreNLP to run CoreNLP Server in the background. 

A sentence can be passed to the `sofia` object using the `.getOutputOnline` method. This returns `results` which is an array of JSON objects where each object in the array represents each sentence provided to the reader.

Additionally, query based reading can be performed with:

```
query = ['food security', 'malnutrition', 'starvation', 'famine', 'mortality', 'die', 'conflict', 'IPC phase', 'flood']
q_results = sofia.writeQueryBasedOutput(sentence, query)
```

Where `q_results` is an array of JSON objects representing the results of query based reading. This can be written to Excel with:

```
sofia.results2excel('q_output.xlsx', q_results)
```