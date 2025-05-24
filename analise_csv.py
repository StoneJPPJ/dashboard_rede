import pandas as pd
import os

def analisar_arquivo(arquivo):
    print(f"\nAnalisando arquivo: {arquivo}")
    try:
        # Tentar diferentes encodings
        encodings = ['utf-8', 'latin1', 'iso-8859-1']
        for encoding in encodings:
            try:
                # Ler apenas as primeiras linhas
                df = pd.read_csv(arquivo, encoding=encoding, nrows=5)
                print(f"\nEncoding usado: {encoding}")
                print("\nColunas encontradas:")
                for col in df.columns:
                    print(f"- {col}")
                print("\nPrimeiras linhas:")
                print(df.head())
                print("\nInformações do DataFrame:")
                print(df.info())
                return
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Erro com encoding {encoding}: {str(e)}")
                continue
    except Exception as e:
        print(f"Erro ao analisar arquivo: {str(e)}")

# Listar todos os arquivos CSV no diretório
arquivos_csv = [f for f in os.listdir('.') if f.endswith('.csv')]

# Analisar cada arquivo
for arquivo in arquivos_csv:
    analisar_arquivo(arquivo) 