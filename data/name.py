import pandas as pd
import requests
from bs4 import BeautifulSoup

# Leitura do ficheiro CSV
df = pd.read_csv('url_data_brasil.csv')

# Função para extrair o nome do site
def extrair_nome_site(url):
    try:
        print(f"Processando URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tenta encontrar o nome do site na tag <title>
        title_tag = soup.find('title')
        if title_tag:
            site_name = title_tag.get_text().strip()
            print(f"Nome do site encontrado na tag <title>: {site_name}")
            return site_name
        
        # Tenta encontrar o nome do site na meta tag og:site_name
        meta_tag = soup.find('meta', property='og:site_name')
        if meta_tag:
            site_name = meta_tag.get('content').strip()
            print(f"Nome do site encontrado na meta tag og:site_name: {site_name}")
            return site_name
        
        # Se não encontrar, retorna 'N/A'
        print(f"Nome do site não encontrado para a URL: {url}")
        return 'N/A'
    except Exception as e:
        print(f"Erro ao processar a URL {url}: {str(e)}")
        return f'Erro: {str(e)}'

# Aplicar a função a cada URL na coluna 'url' e criar uma nova coluna 'site_name' com os nomes dos sites
print("Iniciando a extração dos nomes dos sites...")
df['site_name'] = df['url'].apply(extrair_nome_site)

# Exibir as primeiras linhas do DataFrame resultante
print("Processo de extração concluído. Primeiras linhas do DataFrame resultante:")
print(df.head())

# Opcional: Salvar o DataFrame resultante em um novo ficheiro CSV
df.to_csv('url_data_with_site_names.csv', index=False)
print("Resultados salvos em 'url_data_with_site_names.csv'")
