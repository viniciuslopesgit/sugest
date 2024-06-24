import pandas as pd

# Carregar o arquivo CSV
file_path = 'url_data_brasil.csv'
df = pd.read_csv(file_path)

# Remover a coluna 'domain'
df.drop(columns=['domain'], inplace=True)

# Salvar o arquivo CSV atualizado
output_file = 'url_data_without_domain.csv'
df.to_csv(output_file, index=False)

print(f"Arquivo CSV sem a coluna 'domain' salvo em: {output_file}")
