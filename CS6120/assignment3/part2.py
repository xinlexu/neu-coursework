import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import brown
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# download all
nltk.download()

# 1. Sentence incorrectly tagged by the POS tagger
sentence = "The complex houses married and single soldiers and their families."
words = word_tokenize(sentence)
tags = nltk.pos_tag(words)

print("POS Tags:")
for word, tag in tags:
    print(f'{word}: {tag}')

print("\nCorrected POS Tags:")
corrected_tags = [
    ('The', 'DT'),
    ('complex', 'NN'),
    ('houses', 'VBZ'),
    ('married', 'JJ'),
    ('and', 'CC'),
    ('single', 'JJ'),
    ('soldiers', 'NNS'),
    ('and', 'CC'),
    ('their', 'PRP$'),
    ('families', 'NNS'),
    ('.', '.')
]
for word, tag in corrected_tags:
    print(f'{word}: {tag}')

# Explanation:
print("\nExplanation:")
print('The word "complex" should be tagged NN (noun) instead of JJ (adjective).')
print('The word "houses" should be tagged VBZ (verb) instead of NNS (noun).')

# 2.
# nltk.corpus.brown.tagged_words()
brown_tagged_words = brown.tagged_words(tagset='universal')[:10000]
brown_words = [word for word, tag in brown_tagged_words]
gold_tags = [tag for word, tag in brown_tagged_words]

# Predict tags nltk.pos_tag()
predicted_tags = [tag for word, tag in nltk.pos_tag(brown_words, tagset='universal')]

# Confusion matrix generate
labels = ['NOUN', 'VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'NUM', 'CONJ', 'PRT', '.', 'X']
cm = confusion_matrix(gold_tags, predicted_tags, labels=labels)

# Plot confusion matrix
plt.figure(figsize=(12, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Reds',
            xticklabels=labels, yticklabels=labels)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix of POS Tagging')
plt.show()

# Discussion
print("\nDiscussion:")
print("The confusion matrix shows that nouns and verbs are generally correctly predicted.")
print("However, adjectives are sometimes mistaken for nouns, and adverbs for adjectives.")
print('For example, the word "back" can be a noun, a verb, an adverb, or an adjective, depending on context.')
