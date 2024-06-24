import pandas as pd
import os

# Carregar o arquivo CSV original
df = pd.read_csv('url_data.csv')

# Definir os principais domínios de topo
top_domains = {
    'br': 'brasil',
    'pt': 'portugal',
    'us': 'eua',
    'ca': 'canada',
    'uk': 'reino_unido',
    'de': 'alemanha',
    'fr': 'franca',
    'it': 'italia',
    'es': 'espanha',
    'jp': 'japao',
    'cn': 'china',
    'in': 'india',
    'ru': 'russia',
    'au': 'australia',
    'com': 'comercial',
    'org': 'organizacao',
    'net': 'network',
    'edu': 'educacao',
    'gov': 'governo',
    'mil': 'militar',
    'info': 'informacao',
    'biz': 'negocios',
    'name': 'nome',
    'pro': 'profissional'
}

# Função para extrair o domínio de uma URL
def extract_domain(url):
    try:
        domain = url.split('.')[-1]
        return domain
    except:
        return None

# Adicionar uma coluna ao DataFrame para os domínios extraídos
df['domain'] = df['url'].apply(extract_domain)

# Criar arquivos separados para cada domínio de topo
for domain, country in top_domains.items():
    domain_df = df[df['domain'] == domain]
    if not domain_df.empty:
        filename = f'url_data_{country}.csv'
        domain_df.to_csv(filename, index=False)
        print(f'Arquivo {filename} salvo com sucesso.')

