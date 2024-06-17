import pandas as pd

# Função para verificar se a URL é de um motor de busca
def is_search_engine(url):
    search_engines = [
        "google.", "bing.", "yahoo.", "baidu.", "duckduckgo.", "yandex.", "ask.", "aol."
    ]
    return any(engine in url for engine in search_engines)

# Carrega o arquivo CSV
df = pd.read_csv("url_data.csv")

# Filtra as linhas, mantendo apenas aquelas cujas URLs não são de motores de busca
df_filtered = df[~df['url'].apply(is_search_engine)]

# Salva o DataFrame filtrado de volta no arquivo CSV
df_filtered.to_csv("url_data_filtered.csv", index=False)

print("Linhas com URLs de motores de busca foram removidas e o novo arquivo foi salvo como 'url_data_filtered.csv'.")
