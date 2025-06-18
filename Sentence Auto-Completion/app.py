import streamlit as st
import tensorflow as tf
import numpy as np
import pickle
from tensorflow.keras.preprocessing.sequence import pad_sequences

model = tf.keras.models.load_model('my_model.keras')

with open('tokenizer.pkl', 'rb') as f:
    tokenizer = pickle.load(f)

max_sequence_len = 16  

def predict_top_five_words(model, tokenizer, seed_text):
    token_list = tokenizer.texts_to_sequences([seed_text])[0]
    token_list = pad_sequences([token_list], maxlen=max_sequence_len-1, padding='pre')
    predicted = model.predict(token_list, verbose=0)
    top_five_indexes = np.argsort(predicted[0])[::-1][:5]
    top_five_words = []
    for index in top_five_indexes:
        for word, idx in tokenizer.word_index.items():
            if idx == index:
                top_five_words.append(word)
                break
    return top_five_words

st.title('Sentence Auto-Completion')

input_text = st.text_input('Enter your sentence:')

if st.button('Predict'):
    if input_text:
        predictions = predict_top_five_words(model, tokenizer, input_text)
        
        st.subheader('Top 5 Predictions:')
        for i, word in enumerate(predictions, 1):
            st.write(f"{i}. {input_text} {word}")
    else:
        st.warning('Please enter a sentence first.')