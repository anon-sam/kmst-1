from copy import copy
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import os
import nltk
from nltk.corpus import treebank
import spacy
from spacy import displacy
from nltk import Tree
#import pudb
from nltk import Tree
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer

porter_stemmer = PorterStemmer()
stop_words = ['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 'here', 'than' ,'this' ,'where', 'many', 'much'] 

en_nlp = spacy.load('en')

def entity_recogniser ( text , printer=True) :
	text_spotlight = copy(text)
	text_spotlight = text_spotlight.replace(" ","%20").replace(",","%2C").replace("?","%3F")

	r = os.popen('curl -sX GET "https://api.dbpedia-spotlight.org/en/spot?text='+text_spotlight+'" -H  "accept: application/json"').read()
	try:
	  r = json.loads(r)['annotation']['surfaceForm']
	  if type(r) is dict:
	  	r = [r]
	except:
	  r = []
	# print(r)

	spotlight_ners=[]
	spotlight_ners_capitalised=[]
	spotlight_ners_hyphenated=[]

	for each in r:
		text_here = each['@name']
		spotlight_ners.append(text_here)
		spotlight_ners_capitalised.append(text_here[0].upper()+text_here[1:])
		spotlight_ners_hyphenated.append((text_here[0].upper()+text_here[1:]).replace(" ","_"))

	if printer:
		print("NERs from DBpedia spotlight: "+str(spotlight_ners_hyphenated))

	text_pn = copy(text)

	for i in range(len(spotlight_ners)):
		text_pn = text_pn.replace(spotlight_ners[i], spotlight_ners_hyphenated[i])

	# print("pn_before: "+str(text_pn))
	text_pn_org = copy(text_pn)

	text_pn = text_pn.split()

	entities_org = []
	entities = []
	entity = ""
	entity_now = ""
	entity_found = False
	between = 0

	for i in range(len(text_pn)):
		if i == 0:
			continue
		if text_pn[i][0].isupper():
			entity_found = True
			entity_now+=text_pn[i]+" "
			if i == len(text_pn) - 1:
				entity = entity_now
				entities.append(entity.strip().replace(" ","_"))
				entities_org.append(entity.strip())
		else:
			if (text_pn[i].lower() == "at" or text_pn[i] == "is" or text_pn[i] == "in" or text_pn[i] == "of" or text_pn[i].lower() == "the" or text_pn[i].lower() == "with") and entity_found:
				entity_now+=text_pn[i]+" "
			else:
				entity = entity_now.strip()
				entity_found = False
				if entity!="":
					entities.append(entity.replace(" ","_"))
					entities_org.append(entity)
					entity_now=""
				entity = ""
	if printer:
		print("Entities found: "+str(entities))
	# print(entities_org)

	for i in range(len(entities)):
		entity_org = entities_org[i]
		entity = entities[i]

		text_pn_org = text_pn_org.replace(entity_org, entity)

	if printer:
		print("Hyphenated query: " + text_pn_org)

	return ( entities , text_pn_org )


# for entity in entities:
# 	ind = text.find(entity)
# 	text_here = text[ind:]
# 	num_words = len(text.split())
# 	for i in range(num_words):

def generate_parse_tree( text ):
	#print("text: "+text)
	text_here = text.replace(" ","+").replace("?","%3F").replace(",","%2C")
	r = os.popen('curl -sX GET http://nlp.stanford.edu:8080/parser/index.jsp?query='+text_here+'&parserSelect=English&parse=Parse').read()
	print(r.split('<pre id="parse" class="spacingFree">')[1].split("</pre>")[0])
	


def find_uri( tokens ):
	for token in tokens:
		token = token.replace("_", " ")
		sparql = SPARQLWrapper("http://10.35.32.94:9999/blazegraph/namespace/DBpedia/sparql")
		sparql.setQuery("""
			prefix bds: <http://www.bigdata.com/rdf/search#>
			select ?s ?p ?o ?score ?rank
			where {
			?o bds:search \""""+token+"""\" .
			?o bds:matchAllTerms "true" .
			?o bds:minRelevance "0.25" .
			?o bds:relevance ?score .
			?o bds:maxRank "1000" .
			?o bds:rank ?rank .
			?s ?p ?o .
			}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		#print("result: "+str(results))
		try:
			for i in results['results']['bindings']:
				#print("i: "+str(i))
				if i['rank']['value']=='1':
					print(i['s']['value'])
		except:
			print("URI not found for token "+token)

def predicate_recogniser( query,entities ):
	query = query.strip()
	query = query.strip(",")
	query = query.strip("?")
	query = query.strip(".")
	query = query.strip(":")
	query = query.strip(";")
	query = query.strip()
	tokens = word_tokenize(query) 
	  
	filtered_tokens = [w for w in tokens if not w.lower() in stop_words] 
	  
	# filtered_tokens = [] 
	  
	# for w in tokens: 
	#     if w not in stop_words: 
	#         filtered_tokens.append(w) 
	  

	print("filtered predicates: "+str(filtered_tokens)) 

	entities_l = [w.lower() for w in entities]
	#print("l "+str(entities_l))
	
	raw_predicates= []
	for w in filtered_tokens:
		if w.lower() not in entities_l:
			raw_predicates.append(w)
	print("raw predicates "+str(raw_predicates))
	stemmed_predicates = []

	for w in raw_predicates:
		stemmed_predicates.append(porter_stemmer.stem(w))

	print(stemmed_predicates)
	return stemmed_predicates

text = input("Enter text: ")
entities , hyphenated_text = entity_recogniser(text, printer=False)
generate_parse_tree( hyphenated_text )

text = text.strip()
text = text.strip(",")
text = text.strip("?")
text = text.strip(".")
text = text.strip(":")
text = text.strip(";")
text = text.strip()

entities , hyphenated_text = entity_recogniser(text)

try:
	del os.environ['http_proxy']
except:
	pass

try:
	del os.environ['https_proxy']
except:
	pass

try:
	del os.environ['HTTP_PROXY']
except:
	pass

try:
	del os.environ['HTTPS_PROXY']
except:
	pass

find_uri( entities )
stemmed_predicates = predicate_recogniser(hyphenated_text, entities)
#find_uri( stemmed_predicates )
