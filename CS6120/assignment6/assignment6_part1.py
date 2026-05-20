import pandas as pd
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

fake_df = pd.read_csv('Fake.csv')
real_df = pd.read_csv('True.csv')

fake_df['label'] = 'fake'
real_df['label'] = 'real'

df = pd.concat([fake_df, real_df], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df['text'] = df['title'] + ' ' + df['text']
df = df[['text', 'label']]
df['label'] = df['label'].str.lower()

train_df, temp_df = train_test_split(df, test_size=0.4, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')
model.eval()

def prepare(n):
    examples = []
    num_per_class = n // 2
    fake_examples = train_df[train_df['label'] == 'fake'].head(num_per_class)
    real_examples = train_df[train_df['label'] == 'real'].head(n - num_per_class)
    balanced_df = pd.concat([fake_examples, real_examples]).sample(frac=1, random_state=42)

    for idx, row in balanced_df.iterrows():
        text = row['text'].replace('\n', ' ').strip()
        tokens = tokenizer.tokenize(text)[:50]
        text = tokenizer.convert_tokens_to_string(tokens)
        label = row['label']
        examples.append(f"Input: {text}\nClassification: {label}\n###\n")
    return ''.join(examples)

def generate_prompt(n, example_text):
    prompt = prepare(n)
    example_text = example_text.replace('\n', ' ').strip()
    tokens = tokenizer.tokenize(example_text)[:50]
    example_text = tokenizer.convert_tokens_to_string(tokens)
    prompt += f"Input: {example_text}\nClassification:"
    return prompt

def generate_response(prompt):
    inputs = tokenizer.encode(prompt, return_tensors='pt')
    max_input_length = 1024 - 20
    input_length = inputs.shape[1]

    if input_length > max_input_length:
        inputs = inputs[:, -max_input_length:]

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=input_length + 5,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            do_sample=False,
            temperature=0.0,
        )

    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = generated_text[len(prompt):].split('\n')[0].strip()
    response = response.split()[0] if response else ''
    return response

def normalize_label(label):
    label = label.lower()
    if 'fake' in label:
        return 'fake'
    elif 'real' in label:
        return 'real'
    else:
        return 'unknown'

def score(n, dataset):
    true_labels = []
    pred_labels = []
    for idx, row in dataset.iterrows():
        prompt = generate_prompt(n, row['text'])
        generated_label = generate_response(prompt)
        normalized_label = normalize_label(generated_label)
        true_labels.append(row['label'])
        pred_labels.append(normalized_label)
        print(f"True Label: {row['label']}, Predicted Label: {normalized_label}")
    indices = [i for i, label in enumerate(pred_labels) if label != 'unknown']
    filtered_true_labels = [true_labels[i] for i in indices]
    filtered_pred_labels = [pred_labels[i] for i in indices]
    if filtered_true_labels:
        acc = accuracy_score(filtered_true_labels, filtered_pred_labels)
        print(f"Accuracy with n={n}: {acc}")
        print(classification_report(filtered_true_labels, filtered_pred_labels))
    else:
        print("No valid predictions to evaluate accuracy.")

for n in range(4, 11):
    print(f"\nTesting with n = {n}")
    score(n, val_df.head(20))

n = 6
print(f"\nEvaluating on test set with n = {n}")
score(n, test_df.head(20))


# A small amount of learning is performed with GPT-2 in a fake news classification task, using a dataset of news
# articles labelled as 'fake' or 'true'. A varying number of examples (n from 4 to 10) were prepared to evaluate the
# performance of the model. Despite varying the number of examples, the model consistently predicted the 'fake' label
# for all inputs, with an accuracy of around 50% for different values of n. The model was able to consistently
# predict the 'false' label for all inputs, with an accuracy of about 50% for all inputs. This suggests that without
# fine-tuning, the GPT-2 model would have difficulty distinguishing between 'fake' and 'real' news in this case.



# Part 2 using model ChatGPT

# Coding Problem: Two Sum (LeetCode Easy)
# Prompt:
# Write a Python function that takes an array of integers and a target integer.
# The function should return the indices of the two numbers that add up to the target.

# Model's Solution:
def two_sum(nums, target):
    num_to_index = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_to_index:
            return [num_to_index[complement], i]
        num_to_index[num] = i

# Evaluation: The model provided an optimal O(n) solution using a hash map.

# Coding Problem: Merge k Sorted Lists (LeetCode Hard)
# Prompt:
# Write a Python function that merges k sorted linked lists and returns it as one sorted list.
# Analyze the time complexity.

# Model's Solution:
from heapq import heappush, heappop

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def merge_k_lists(lists):
    heap = []
    for idx, node in enumerate(lists):
        if node:
            heappush(heap, (node.val, idx, node))
    head = tail = ListNode(0)
    while heap:
        val, idx, node = heappop(heap)
        tail.next = node
        tail = tail.next
        if node.next:
            heappush(heap, (node.next.val, idx, node.next))
    return head.next

# Evaluation: The model correctly used a min-heap to efficiently merge the lists.

# Do a Larger Project: Simple Web Scraper
# Prompt:
# Create a simple Python script that scrapes the titles and URLs from the first page of search results on a given website.

# Model's Solution:
# The model advised against scraping websites without permission and suggested using APIs where available.

# Observation:
# Clear, specific advice leads to accurate, optimised code.
# Expertise in algorithmic problems, data structures and providing efficient solutions.
# Need to specify language, required efficiency and any constraints or ethical considerations.


# 2
# Mathematical Proof
# Prompt:
# Provide a detailed proof that the square root of 2 is irrational.

# Model's Response:
# Delivered a thorough proof by contradiction, showing that assuming √2 is rational leads to a contradiction.

# Story Generation
# Prompt:
# Write a short story about an astronaut who discovers a new planet.

# Model's Response:
# Generated a coherent and engaging story about an astronaut's journey and discovery.

# Cover Letter
# Prompt: Write a cover letter for Jane Smith applying for the position of Software Engineer at ABC Tech, emphasizing
# her experience in machine learning and Python.

# Model's Response:
# Produced a professional cover letter highlighting relevant skills and enthusiasm for the role.

# Observations:
# excellent at generating structured, coherent text in a variety of formats.
# tasks requiring up-to-date expertise or real-time data.
# Language models perform better on tasks involving linguistic patterns and common sense, but may struggle with current or specialised information.
