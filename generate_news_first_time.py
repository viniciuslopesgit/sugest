# generate_news_first_time.py

from create_db import get_database_connection
import pandas as pd
import random

def generate_news_urls(user_id):
    conn = get_database_connection()  # Usa a função para obter a conexão
    c = conn.cursor()
    
    c.execute('SELECT * FROM user_urls WHERE user_id = %s', (user_id,))
    urls = c.fetchall()
    conn.close()
    
    if not urls:  # Se não houver URLs associadas ao usuário
        # Carregar o arquivo CSV
        news_data = pd.read_csv('data/news.csv')
        
        # Selecionar aleatoriamente 5 URLs
        selected_urls = random.sample(news_data['url'].tolist(), 5)
        
        # Inserir os URLs gerados no banco de dados com a avaliação inicial
        conn = get_database_connection() 
        # Usa a função para obter a conexão
        c = conn.cursor()

        for url in selected_urls:
            c.execute('INSERT INTO user_urls (user_id, url, rate) VALUES (%s, %s, %s)', (user_id, url, 0))
        conn.commit()
        conn.close()
        
        return selected_urls
    else:
        return [url[2] for url in urls]  # Retorna as URLs já salvas no banco de dados
