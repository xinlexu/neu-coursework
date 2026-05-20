import pandas as pd
import numpy as np
import re
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Read the datasets
df_real = pd.read_csv('True.csv')
df_real['RealNews?'] = True
df_fake = pd.read_csv('Fake.csv')
df_fake['RealNews?'] = False

# Combine datasets
df = pd.concat([df_real, df_fake], ignore_index=True)

# first five rows of the dataframe
print(df.head())
# verify that you have all 44,898 rows
print("Total number of rows:", len(df))

# create a new column for the entire document (title + text)
df['document'] = df[['title', 'text']].agg(' '.join, axis=1)

# ignore case for this assignment
df['document'] = df['document'].apply(lambda x: x.lower())

# Split the dataframe into training and test sets
df_train, df_test = train_test_split(df, test_size=0.2, shuffle=True)


def tokenize(document):
    # Use a regular expression such as re.split(r"\W+", document) to tokenize documents
    tokens = re.split(r"\W+", document)
    tokens = [token for token in tokens if token]
    return tokens


# Tokenize the training documents
df_train['tokens'] = df_train['document'].apply(tokenize)

# Part1

# Initialize word frequency dictionaries
real_word_counts = defaultdict(int)
fake_word_counts = defaultdict(int)
real_total_words = 0
fake_total_words = 0

# Calculate word frequencies and total word counts
for tokens, is_real in zip(df_train['tokens'], df_train['RealNews?']):
    if is_real:
        for token in tokens:
            real_word_counts[token] += 1
            real_total_words += 1
    else:
        for token in tokens:
            fake_word_counts[token] += 1
            fake_total_words += 1

# Calculate prior probabilities
total_documents = len(df_train)
real_docs = df_train['RealNews?'].sum()
fake_docs = total_documents - real_docs

prior_real = real_docs / total_documents
prior_fake = fake_docs / total_documents

# Create the vocabulary
vocabulary = set(real_word_counts.keys()).union(set(fake_word_counts.keys()))
vocab_size = len(vocabulary)


def classify(document):
    tokens = tokenize(document)
    real_prob = np.log(prior_real)
    fake_prob = np.log(prior_fake)

    for token in tokens:
        # Calculate likelihoods with Laplace smoothing
        real_token_count = real_word_counts.get(token, 0) + 1
        real_prob += np.log(real_token_count / (real_total_words + vocab_size))

        fake_token_count = fake_word_counts.get(token, 0) + 1
        fake_prob += np.log(fake_token_count / (fake_total_words + vocab_size))

    return real_prob > fake_prob


# Predict on the test set
df_test['predicted'] = df_test['document'].apply(classify)

# Evaluate the model
y_true = df_test['RealNews?'].astype(int)
y_pred = df_test['predicted'].astype(int)
precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')

print("Naive Bayes Classifier Performance:")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")

# Part 2
# Calculate df
word_doc_freq = defaultdict(int)
for tokens in df_train['tokens']:
    unique_tokens = set(tokens)
    for token in unique_tokens:
        word_doc_freq[token] += 1

# Build vocabulary with words appear at least twice
vocabulary = [word for word, freq in word_doc_freq.items() if freq >= 2]
vocab_size = len(vocabulary)
word_to_index = {word: idx for idx, word in enumerate(vocabulary)}

# Calculate IDF vector
total_docs = len(df_train)
idf_vector = np.zeros(vocab_size)
for word, idx in word_to_index.items():
    df_count = word_doc_freq[word]
    idf_vector[idx] = np.log((total_docs + 1) / (df_count + 1)) + 1  # Smoothing


def compute_tf(tokens):
    tf_vector = np.zeros(vocab_size)
    token_counts = defaultdict(int)
    for token in tokens:
        if token in word_to_index:
            token_counts[token] += 1
    for token, count in token_counts.items():
        idx = word_to_index[token]
        tf_vector[idx] = count
    # Normalize TF vector
    tf_vector /= len(tokens)
    return tf_vector


# Compute TF-IDF for the training set
X_train = np.array([compute_tf(tokens) * idf_vector for tokens in df_train['tokens']])
y_train = df_train['RealNews?'].astype(int).values

# Train logistic regression model
clf = LogisticRegression(random_state=0, max_iter=1000)
clf.fit(X_train, y_train)

# Tokenize
df_test['tokens'] = df_test['document'].apply(tokenize)

# Compute TF-IDF for the test set
X_test = np.array([compute_tf(tokens) * idf_vector for tokens in df_test['tokens']])
y_test = df_test['RealNews?'].astype(int).values

# Make predictions and evaluate
y_pred = clf.predict(X_test)
precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')

print("Logistic Regression (Manual TF-IDF) Classifier Performance:")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")

# Part 3
X_train_documents = df_train['document']
X_test_documents = df_test['document']
y_train = df_train['RealNews?'].astype(int).values
y_test = df_test['RealNews?'].astype(int).values

# Naive Bayes with CountVectorizer
vectorizer = CountVectorizer()
X_train_counts = vectorizer.fit_transform(X_train_documents)
X_test_counts = vectorizer.transform(X_test_documents)

clf_nb = MultinomialNB()
clf_nb.fit(X_train_counts, y_train)
y_pred_nb = clf_nb.predict(X_test_counts)

precision_nb, recall_nb, f1_nb, _ = precision_recall_fscore_support(y_test, y_pred_nb, average='binary')

print("Naive Bayes (Scikit-learn) Classifier Performance:")
print(f"Precision: {precision_nb:.4f}")
print(f"Recall: {recall_nb:.4f}")
print(f"F1 Score: {f1_nb:.4f}")

# Logistic Regression with TfidfVectorizer
tfidf_vectorizer = TfidfVectorizer()
X_train_tfidf = tfidf_vectorizer.fit_transform(X_train_documents)
X_test_tfidf = tfidf_vectorizer.transform(X_test_documents)

clf_lr = LogisticRegression(random_state=0, max_iter=1000)
clf_lr.fit(X_train_tfidf, y_train)
y_pred_lr = clf_lr.predict(X_test_tfidf)

precision_lr, recall_lr, f1_lr, _ = precision_recall_fscore_support(y_test, y_pred_lr, average='binary')

print("Logistic Regression (Scikit-learn TF-IDF) Classifier Performance:")
print(f"Precision: {precision_lr:.4f}")
print(f"Recall: {recall_lr:.4f}")
print(f"F1 Score: {f1_lr:.4f}")

# Experiment with ngram_range parameter
tfidf_vectorizer_ngram = TfidfVectorizer(ngram_range=(1, 2))
X_train_tfidf_ngram = tfidf_vectorizer_ngram.fit_transform(X_train_documents)
X_test_tfidf_ngram = tfidf_vectorizer_ngram.transform(X_test_documents)

clf_lr_ngram = LogisticRegression(random_state=0, max_iter=1000)
clf_lr_ngram.fit(X_train_tfidf_ngram, y_train)
y_pred_lr_ngram = clf_lr_ngram.predict(X_test_tfidf_ngram)

precision_ngram, recall_ngram, f1_ngram, _ = precision_recall_fscore_support(y_test, y_pred_lr_ngram, average='binary')

print("Logistic Regression (ngram_range=(1,2)) Classifier Performance:")
print(f"Precision: {precision_ngram:.4f}")
print(f"Recall: {recall_ngram:.4f}")
print(f"F1 Score: {f1_ngram:.4f}")

# experiment with the stop_words parameter

tfidf_vectorizer_default = TfidfVectorizer()
X_train_tfidf_default = tfidf_vectorizer_default.fit_transform(X_train_documents)
X_test_tfidf_default = tfidf_vectorizer_default.transform(X_test_documents)

clf_default = LogisticRegression(random_state=0, max_iter=1000)
clf_default.fit(X_train_tfidf_default, y_train)
y_pred_default = clf_default.predict(X_test_tfidf_default)

precision_default, recall_default, f1_default, _ = precision_recall_fscore_support(y_test, y_pred_default,
                                                                                   average='binary')

print("Model performance with default parameters:")
print(f"Precision: {precision_default:.4f}")
print(f"Recall: {recall_default:.4f}")
print(f"F1 Score: {f1_default:.4f}")

# TfidfVectorizer with stop_words='english'
tfidf_vectorizer_sw = TfidfVectorizer(stop_words='english')
X_train_tfidf_sw = tfidf_vectorizer_sw.fit_transform(X_train_documents)
X_test_tfidf_sw = tfidf_vectorizer_sw.transform(X_test_documents)

clf_sw = LogisticRegression(random_state=0, max_iter=1000)
clf_sw.fit(X_train_tfidf_sw, y_train)
y_pred_sw = clf_sw.predict(X_test_tfidf_sw)

precision_sw, recall_sw, f1_sw, _ = precision_recall_fscore_support(y_test, y_pred_sw, average='binary')

print("Model performance after applying stop_words parameter:")
print(f"Precision: {precision_sw:.4f}")
print(f"Recall: {recall_sw:.4f}")
print(f"F1 Score: {f1_sw:.4f}")

# Compare results
print("\nPerformance comparison:")
print(f"Precision improvement: {precision_sw - precision_default:.4f}")
print(f"Recall improvement: {recall_sw - recall_default:.4f}")
print(f"F1 Score improvement: {f1_sw - f1_default:.4f}")

# Briefly explain what the parameter is and show how it affected the scores when you changed it.

# The 'stop_words' parameter in TfidfVectorizer allows us to specify a list of words to be ignored during text vectorization.
# Those stop words ('the', 'is', 'at', etc.) that don't usually contribute much on meaning.
# By setting stop_words='english', we use a built-in list of English stop words to exclude.

# Observed slightly decrease in model performance compared to the default settings after applying the stop_words parameter.

# Model Performance with Default Parameters:
# Precision: 0.9843
# Recall: 0.9854
# F1 Score: 0.9849
# Model Performance after Applying stop_words='english':
#
# Precision: 0.9824
# Recall: 0.9843
# F1 Score: 0.9834
# Performance Comparison:
#
# Precision improvement: -0.00186
# Recall improvement: -0.00117
# F1 Score improvement: -0.00152

# By using the stop_words parameter, model's precision decreased by approximately 0.19%, recall decreased by 0.12%,
# and F1 score decreased by 0.15%. It appears that removing stop words slightly reduced the model's ability to
# correctly identify real news articles.

# Possible reason:
# Stop words may still contribute to the context or structure of sentences.
# Removing them reduces the feature space, potentially losing useful information.

# Conclusion
# Experiment shows that keeping stop words in the feature set was beneficial for the fake news detection in this case.
