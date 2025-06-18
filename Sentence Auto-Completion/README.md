# Sentence Auto-Completion using NLP

This project demonstrates a **Sentence Auto-Completion** system built using **Natural Language Processing (NLP)** techniques. The model predicts the next word in a sentence using a trained N-gram language model.

## 🚀 Features

- Predicts the next word(s) in a sentence
- Trained on a sample corpus using NLP techniques
- Uses N-gram modeling (up to trigrams)
- Basic user interface for input and suggestions

## 🧠 How It Works

1. The text corpus is tokenized into words.
2. An N-gram model (unigram, bigram, trigram) is built.
3. Based on the last one or two words of the input, the model predicts the most probable next word.
4. The model uses probability and frequency of occurrence to make predictions.

## 🔧 Installation

1. Clone the repository:

```bash
git clone https://github.com/krunal-lw/AI-ML-Demo.git
cd AI-ML-Demo/Sentence\ Auto-Completion
```

2. Create a virtual environment and activate it (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install numpy panda nltk tensorflow
```

## 🧪 Usage

Open the Jupyter notebook:

```bash
streamlit run app.py
```

## 📚 Example

```
Input  : "The sun is"
Output : "shining"
```

## ✅ Requirements

- Python 3.10
- nltk
- numpy
- pandas
- Jupyter Notebook

Install all requirements via `pip install numpy panda nltk tensorflow`.

## 📝 Notes

- The quality of predictions depends on the size and variety of the training corpus.
- You can replace `corpus.txt` with any large text file (e.g., books, articles) to train the model on a different dataset.

## 🤝 Contributing

Contributions are welcome! Feel free to fork this repository, make enhancements, and submit a pull request.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
