import pandas as pd 
import spacy
import nltk
import re

import numpy as np
import itertools

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from spacy import displacy
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
from nltk.stem import WordNetLemmatizer
from nltk.tree import Tree

import collections
from collections import Counter

"""
    Convert string of helpful to int, then sort data
"""

def get_number_from_string(string):
    return re.search(r'\d+', string)

def rearrange_by_helpful(reviews):
    reviews.dropna(inplace=True)
    reviews.reset_index(drop = True, inplace = True)
    for index,string in enumerate(reviews.helpful):
        num = 0
        if "One" in string:
            num = 1
        elif get_number_from_string(string) != None:
            num = int(get_number_from_string(string)[0])

        reviews.helpful[index] = num

    reviews = reviews.sort_values(by=['helpful'], ascending = False)
    reviews.reset_index(drop = True, inplace = True)
    return reviews

"""
    Get n aspects from each reviews
"""
def get_aspects(nlp, stop_words, review, number):
    # Use space to process review
    doc = nlp(review, disable = ['ner', 'parser'])
    # Get POS of each word
    pos = [word.pos_ for word in doc]
    # Remove common words and retain only nouns
    doc = [word.text for word in doc if (word.text not in stop_words) and (word.pos_=="NOUN")]
    # Normalize text to lower case
    doc = list(map(lambda i: i.lower(), doc))
    doc = pd.Series(doc)
    # Get 5 most frequent nouns
    aspects = doc.value_counts().head(number).index.tolist()

    return aspects

"""
    Get list of aspects from reviews dataframe
"""

def get_list_of_aspects(nlp, stop_words, reviews, number_of_aspect = 5):
    aspects = []
    for review in reviews.reviewBody:
        aspects.extend(get_aspects(nlp, stop_words, review, number_of_aspect))
        count = Counter(aspects)

    sort_count_aspects = count.most_common()
    return sort_count_aspects

"""
    Proprocess reviews to correct index of punkts.
    Input: paragraph/review 
    Example : I like tomato . Do u like it ? -> I like tomato. Do you like it?
    What for? -> sentence-tokenize
"""
def preprocess(text):
    punkt_list = ['.', '(', ')', '?', ':']
    res = ""    
    for index in range(len(text)-1):
        res = res + text[index]
        if text[index] in punkt_list:
            if text[index+1].isalpha():
                res = res + ' '
    return res

"""
    Take list of aspects, list of chunks sents
    For each aspects, find chunk_sents appropriately 
"""
def aspect_to_sents(sort_count_aspects=None, list_chunk_token=None):
    aspect_to_sents = {}
    for aspect in sort_count_aspects:
        if aspect[1] < 10:
            return aspect_to_sents
        
        summary_sents = []
        for chunk in list_chunk_token:
            if aspect[0] in chunk:
                sent = " ".join(chunk)
                if not sent.endswith('.'):
                    sent = sent + '.'
                summary_sents.append(sent)
                # remove which sent used for iterated aspect
                list_chunk_token.remove(chunk)
        aspect_to_sents[aspect[0]] = summary_sents

"""
    Input: reviews
    output : List of chunk token
"""
def get_list_chunk_sents(reviews):
    wordnet_lemmatizer = WordNetLemmatizer()
    grammar = r"""
                SENT: 
                    {<DT>?<JJ>*<NN.*>+<V.*>*<DT>?<RB.*>?<JJ>+<.*>*}
                    {<DT>?<NN.*><V.*><IN><CD>?<NN.*><.*>*}
                """
            # {<DT>?<JJ>*<NN.?>+<V.*>*<RB>?<JJ>+}
    tree_list = []
    for review in reviews.reviewBody:
        sentence = preprocess(review)
        sents = nltk.sent_tokenize(sentence)
        for sent in sents:
            words = nltk.word_tokenize(sent)
            pos_tag = nltk.pos_tag(words)
                
            cp = nltk.RegexpParser(grammar)
            result = cp.parse(pos_tag)

            for subtree in result.subtrees():
                if subtree.label() == 'SENT' or subtree.label()=='NP':
                    tree_list.append(subtree)

    list_chunk = []
    for item in tree_list:
        s = ""
        for word_pos in item.leaves():
            s = s + word_pos[0] + " "
        list_chunk.append(s)

    list_chunk_token = []
    for s in list_chunk:
        s_token = nltk.word_tokenize(s) 
        list_chunk_token.append(s_token)

    return list_chunk_token

"""
    Find a list of sentences, which is dai dien cho nhung aspects
"""
def max_sum_sim(doc_embedding, candidate_embeddings, candidates, top_n, nr_candidates):
    # Calculate distances and extract keywords
    distances = cosine_similarity(doc_embedding, candidate_embeddings)
    distances_candidates = cosine_similarity(candidate_embeddings,candidate_embeddings)

    # Get top_n words as candidates based on cosine similarity
    words_idx = list(distances.argsort()[0][-nr_candidates:])
    words_vals = [candidates[index] for index in words_idx]
    distances_candidates = distances_candidates[np.ix_(words_idx, words_idx)]

    # Calculate the combination of words that are the least similar to each other
    min_sim = np.inf
    candidate = None
    for combination in itertools.combinations(range(len(words_idx)), top_n):
        sim = sum([distances_candidates[i][j] for i in combination for j in combination if i != j])
        if sim < min_sim:
            candidate = combination
            min_sim = sim
    return [words_vals[idx] for idx in candidate]



class FaceExtraction:
    def __init__(self):
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        self.model_sent_trans = SentenceTransformer('paraphrase-distilroberta-base-v1')
        # Load nlp model english
        self.nlp = spacy.load("en_core_web_lg")
       

    """
        Main function
    """
    def factExtract(self, file_path):
        
        # Read file csv in data folder 
        with open(file_path, 'r') as f:
            reviews = pd.read_csv(f)

        # Change helpful to number and sort
        reviews = rearrange_by_helpful(reviews)

        stop_words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", 
                    "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", 
                    "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", 
                    "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", 
                    "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", 
                    "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", 
                    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", 
                    "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", 
                    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
                    "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

        # -------------------------------------------------------------
        # Using cosine_similarity to find 5 best sentences fit all others sentences for each aspect
        sort_count_aspects = get_list_of_aspects(self.nlp, stop_words, reviews)
        list_chunk_token = get_list_chunk_sents(reviews)
        aspect_sents = aspect_to_sents(sort_count_aspects, list_chunk_token)
        
        top_n = 5
        summary_reviews = {}
        for index,aspect in enumerate(aspect_sents):
            if index > 10:
                return summary_reviews
            # summary_reviews = summary_reviews + aspect + '\n'
            summary_reviews[aspect] = []
            values = aspect_sents[aspect]
            if len(values) == 0:
                continue
            doc = ""
            for s in values:
                doc = doc + " " + s.rstrip()

            doc_embedding = self.model_sent_trans.encode([doc])
            sents_embedding = self.model_sent_trans.encode(values)

            max_sum_sents = max_sum_sim(doc_embedding, sents_embedding, values, min(len(values),top_n), min(len(values),20))
            # print(len(max_sum_sents))
            if len(max_sum_sents)>0:
                summary_reviews[aspect] = []
                for sent in max_sum_sents:
                    summary_reviews[aspect].append(sent)
        return summary_reviews