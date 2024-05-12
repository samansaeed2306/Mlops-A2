from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import csv
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
import nltk

# Download NLTK resources
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Function to scrape links, titles, and descriptions from a webpage
def scrape_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extracting links, titles, and descriptions
    links = []
    titles = []
    descriptions = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.startswith('http'):
            links.append(href)
            title = link.get_text(strip=True)
            titles.append(title)
            # Extracting description if available
            description = link.find_next_sibling(string=True)
            if description and len(description.strip()) > 0:
                descriptions.append(description.strip())
            else:
                descriptions.append("")
    
    return links, titles, descriptions

# Function to preprocess text
def preprocess_text(text):
    """
    Preprocess text by removing HTML tags, punctuation, stop words, and performing stemming and lemmatization.

    Args:
        text (str): The text to preprocess.

    Returns:
        tuple: A tuple containing lists of stemmed tokens and lemmatized tokens.
    """
    # Remove HTML tags
    text = re.sub('<[^<]+?>', '', text)
    # Remove punctuation and special characters
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Convert to lowercase
    text = text.lower()
    # Tokenization
    tokens = word_tokenize(text)
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    # Stemming and Lemmatization
    stemmer = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return stemmed_tokens, lemmatized_tokens

# Function to write preprocessed data into CSV
def write_to_csv(task_instance):
    """
    Write preprocessed data into a CSV file.

    Args:
        task_instance: Airflow task instance.

    Returns:
        str: A message indicating the status of CSV writing.
    """
    preprocessed_dawn_titles = []  # Assume this is defined elsewhere
    preprocessed_dawn_descriptions = []  # Assume this is defined elsewhere
    preprocessed_bbc_titles = []  # Assume this is defined elsewhere
    preprocessed_bbc_descriptions = []  # Assume this is defined elsewhere

    try:
        with open('dataExtracted.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Website', 'Title', 'Lemmatized Title', 'Description', 'Lemmatized Description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Write Dawn data
            for title, description in zip(preprocessed_dawn_titles, preprocessed_dawn_descriptions):
                writer.writerow({'Website': 'Dawn',
                                 'Title': ' '.join(title[0]),  # Join stemmed tokens
                                 'Lemmatized Title': ' '.join(title[1]),  # Join lemmatized tokens
                                 'Description': ' '.join(description[0]),  # Join stemmed tokens
                                 'Lemmatized Description': ' '.join(description[1])})  # Join lemmatized tokens

            # Write BBC data
            for title, description in zip(preprocessed_bbc_titles, preprocessed_bbc_descriptions):
                writer.writerow({'Website': 'BBC',
                                 'Title': ' '.join(title[0]),  # Join stemmed tokens
                                 'Lemmatized Title': ' '.join(title[1]),  # Join lemmatized tokens
                                 'Description': ' '.join(description[0]),  # Join stemmed tokens
                                 'Lemmatized Description': ' '.join(description[1])})  # Join lemmatized tokens

        return "Data has been saved to 'dataExtracted.csv'."

    except Exception as e:
        return f"Error occurred while writing to CSV: {str(e)}"


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 12),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

dag = DAG(
    'web_scraping_dag',
    default_args=default_args,
    description='A DAG to automate web scraping, data preprocessing, and CSV writing',
    schedule_interval='@daily',
)

scrape_dawn_task = PythonOperator(
    task_id='scrape_dawn',
    python_callable=scrape_data,
    op_kwargs={'url': 'https://www.dawn.com/'},
    dag=dag,
)

scrape_bbc_task = PythonOperator(
    task_id='scrape_bbc',
    python_callable=scrape_data,
    op_kwargs={'url': 'https://www.bbc.com/'},
    dag=dag,
)

preprocess_task = PythonOperator(
    task_id='preprocess_data',
    python_callable=preprocess_text,
    op_args=['text'],  # Pass the required text as an argument
    dag=dag,
)

write_to_csv_task = PythonOperator(
    task_id='write_to_csv',
    python_callable=write_to_csv,
    provide_context=True,  # Pass task instance to the function
    dag=dag,
)

# Define task dependencies
scrape_dawn_task >> preprocess_task
scrape_bbc_task >> preprocess_task
preprocess_task >> write_to_csv_task
