import pandas as pd
import requests
from bs4 import BeautifulSoup

# Carregar o arquivo CSV
data = pd.read_csv('url_data_brasil.csv')

# Função para obter a descrição da página
def get_description(url):
    try:
        response = requests.get(url, timeout=1)  # Timeout para evitar demoras
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Tentar pegar a meta tag description
            description_tag = soup.find('meta', attrs={'name': 'description'})
            if description_tag and 'content' in description_tag.attrs:
                description = description_tag['content']
                return description[:100]  # Limitar a 100 caracteres
        return ''
    except Exception:
        return ''

# Aplicar a função a cada URL e salvar a descrição na coluna 'description'
data['description'] = data['url'].apply(get_description)

# Salvar o DataFrame atualizado de volta para um arquivo CSV
data.to_csv('url_data_portugal_updated.csv', index=False)
