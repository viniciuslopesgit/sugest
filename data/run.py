import pandas as pd

# Passo 1: Ler o arquivo CSV
file_path = 'url_data.csv'  # Substitua pelo caminho do seu arquivo
df = pd.read_csv(file_path)

# Passo 2: Identificar as colunas que contêm 'location', 'timezone' e 'language'
cols_to_remove = [col for col in df.columns if any(keyword in col.lower() for keyword in ['location', 'timezone', 'language'])]

# Passo 3: Remover essas colunas
df_cleaned = df.drop(columns=cols_to_remove)

# Passo 4: Salvar o novo arquivo CSV
df_cleaned.to_csv('url_data_cleaned.csv', index=False)

print("As colunas foram removidas e o arquivo foi salvo como 'url_data_cleaned.csv'.")

