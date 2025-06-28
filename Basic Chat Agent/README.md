# Basic Chat Agent using NLP

## 📁 Project Structure

```
Basic Chat Agent/
│
├── main.py                      # Main implementation in Jupyter Notebook
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/krunal-lw/AI-ML-Demo.git
cd AI-ML-Demo/Basic\ Chat\ Agent
```

### 2. Set Up Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
### 4. create .env file in root directory
```bash
OPENAI_API_KEY=your_api_key
GOOGLE_APPLICATION_CREDENTIALS = path_to_your_credentials.json
```
### 5. How to download credentials.json file and and copy api key
```bash
Step 1: Create a Google Cloud Project
    1. Go to the Google Cloud Console https://console.cloud.google.com/
    2. Click on the project dropdown at the top of the page
    3. Click "New Project"
    4. Enter a name for your project and click "Create"

Step 2: Enable the Gemini API
    1. In your Google Cloud project, go to "APIs & Services" > "Library"
    2. Search for "Gemini API" or "Generative Language API"
    3. Click on the API and then click "Enable"

Step 3: Create Service Account Credentials
    1. Go to "APIs & Services" > "Credentials"
    2. Click "Create Credentials" > "Service Account"
    3. Enter a name for your service account
    4. Click "Create and Continue"
    5. For the role, select "Basic" > "Editor" (or a more restrictive role if preferred)
    6. Click "Continue" and then "Done"

Step 4: Generate and Download the JSON Key File
    1. On the Credentials page, find your newly created service account
    2. Click on the service account name
    3. Go to the "Keys" tab
    4. Click "Add Key" > "Create new key"
    5. Select "JSON" as the key type
    6. Click "Create" - this will download the JSON key file to your computer
    
Step 5: Update Your .env File with the Path to the JSON Key File
    1. Open your.env file in a text editor
    2. Add the following line:
    GOOGLE_APPLICATION_CREDENTIALS=path_to_your_credentials.json
    GOOGLE_API_KEY=your_api_key
    
```

### 4. Run the Chat Agent

```bash
python Chat_Agent.py
```
### 5. Run Front End
```bash
npm install vite
npm run dev
## 🤝 Contributing

Feel free to fork the repository, make improvements, and submit a pull request.

