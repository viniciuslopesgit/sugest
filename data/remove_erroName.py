import pandas as pd

# Ler o arquivo CSV
df = pd.read_csv('url_data_brasil.csv')

# Garantir que todos os valores da coluna 'name' sejam strings
df['name'] = df['name'].astype(str)

# Remover linhas onde a coluna 'name' começa com 'Erro'
df = df[~df['name'].str.startswith('Erro')]

# Salvar o DataFrame resultante de volta em um novo arquivo CSV
df.to_csv('url_data_brasil_filtrado.csv', index=False)
