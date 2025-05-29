import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
import shutil
import calendar
import warnings

# Suprimir warnings específicos de parsing de datas
warnings.filterwarnings('ignore', message='.*Parsing dates in.*')
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')
warnings.filterwarnings('ignore', message='.*dayfirst.*')

# Configurar pandas para não fazer parsing automático de datas
pd.options.mode.chained_assignment = None

# Função utilitária para parsing de datas
def parse_dates_safely(date_series):
    """
    Converte série de datas de forma segura, tentando múltiplos formatos
    """
    try:
        # Primeiro tenta com dayfirst=True
        return pd.to_datetime(date_series, errors='coerce', dayfirst=True)
    except:
        try:
            # Tenta formato específico brasileiro
            return pd.to_datetime(date_series, errors='coerce', format='%d/%m/%Y %H:%M:%S')
        except:
            try:
                # Tenta formato alternativo
                return pd.to_datetime(date_series, errors='coerce', format='%d/%m/%Y')
            except:
                # Último recurso - pandas inferir automaticamente
                return pd.to_datetime(date_series, errors='coerce')

# Diretórios
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide"
)

# Definição global das formas de pagamento a serem excluídas
PAGAMENTOS_EXCLUIDOS = ['DINHEIRO']

# Função auxiliar para converter nome do mês em número
MESES_PT = {
    'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
    'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
}

def mes_ano_para_ordem(mes_ano):
    # Exemplo de mes_ano: 'Março 2025'
    partes = mes_ano.lower().split()
    if len(partes) == 2:
        mes_nome, ano = partes
        mes_num = MESES_PT.get(mes_nome, 0)
        try:
            ano_num = int(ano)
        except:
            ano_num = 0
        return ano_num * 100 + mes_num
    return 0

# Função para validar o nome do arquivo
def validar_nome_arquivo(nome_arquivo):
    try:
        # Remove a extensão .csv
        nome_sem_extensao = nome_arquivo.replace('.csv', '')
        # Divide o nome em mês e ano
        mes, ano = nome_sem_extensao.split('_')
        # Verifica se o ano tem 2 dígitos
        if len(ano) != 2:
            return False
        return True
    except:
        return False

@st.cache_data
def processar_csv(arquivo, mes_nome=None):
    try:
        encodings = ['utf-8', 'latin1', 'iso-8859-1']
        for encoding in encodings:
            try:
                # Suprimir warnings temporariamente durante o carregamento
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    df = pd.read_csv(
                        arquivo,
                        encoding=encoding,
                        sep=';',
                        on_bad_lines='skip',
                        skipinitialspace=True,
                        skip_blank_lines=True,
                        dtype={'VALOR PAGO': str},
                        parse_dates=False,  # Evitar parsing automático de datas
                        date_parser=None    # Não usar parser automático
                    )
                
                # Renomear coluna de valor se necessário
                if 'VALOR PAGO' in df.columns:
                    df = df.rename(columns={'VALOR PAGO': 'VALOR'})
                
                # Processar coluna de valor
                if 'VALOR' in df.columns:
                    df['VALOR'] = df['VALOR'].astype(str).str.replace(r'[^\d.,]', '', regex=True)
                    df['VALOR'] = df['VALOR'].str.replace(',', '.')
                    df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                    df = df.dropna(subset=['VALOR'])
                    df = df[df['VALOR'] >= 0]
                
                # Processar tipo de pagamento
                if 'TIPO DE PAGAMENTO' in df.columns:
                    df['TIPO DE PAGAMENTO'] = df['TIPO DE PAGAMENTO'].astype(str).str.strip().str.upper()
                
                # Tratar coluna de data/hora se existir
                if 'DATA/HORA' in df.columns:
                    # Converter para string primeiro para evitar warnings
                    df['DATA/HORA'] = df['DATA/HORA'].astype(str)
                    # Usar nossa função segura de parsing somente se necessário para análises futuras
                    # Por agora, deixamos como string para evitar warnings durante o carregamento
                
                # Adicionar mês se fornecido
                if mes_nome is not None:
                    df['Mês'] = mes_nome
                
                return df
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        return None
    except Exception as e:
        st.error(f"Erro ao processar o arquivo {arquivo}: {str(e)}")
        return None

def salvar_processado(df, nome_base):
    df.to_parquet(os.path.join(PROCESSED_DIR, nome_base + '.parquet'))

def carregar_processado(nome_base):
    return pd.read_parquet(os.path.join(PROCESSED_DIR, nome_base + '.parquet'))

# Interface principal
st.title("📊 Dashboard de Vendas")

# Seção de upload de arquivo
st.subheader("Upload de Novo Arquivo")
arquivo_upload = st.file_uploader("Selecione um arquivo CSV", type=['csv'])
if arquivo_upload is not None:
    if validar_nome_arquivo(arquivo_upload.name):
        nome_base = arquivo_upload.name.replace('.csv', '')
        caminho_csv = os.path.join(UPLOAD_DIR, arquivo_upload.name)
        with open(caminho_csv, 'wb') as f:
            f.write(arquivo_upload.getvalue())
        with st.spinner("Processando arquivo..."):
            mes, ano = nome_base.split('_')
            mes_nome = f"{mes.capitalize()} 20{ano}"
            df_proc = processar_csv(caminho_csv, mes_nome=mes_nome)
            if df_proc is not None:
                salvar_processado(df_proc, nome_base)
                st.success("Arquivo processado e salvo!")
            else:
                st.error("Erro ao processar o arquivo.")
        st.cache_data.clear()
    else:
        st.error("O nome do arquivo deve seguir o padrão 'mês_ano.csv' (ex: janeiro_25.csv)")

# Mapear meses para arquivos processados
meses_arquivos = {}
for arquivo in os.listdir(PROCESSED_DIR):
    if arquivo.endswith('.parquet'):
        nome_sem_extensao = arquivo.replace('.parquet', '')
        try:
            mes, ano = nome_sem_extensao.split('_')
            mes_nome = mes.capitalize()
            meses_arquivos[f"{mes_nome} 20{ano}"] = arquivo
        except:
            continue

# Obter meses disponíveis e ordenar
meses_disponiveis = sorted(list(meses_arquivos.keys()), key=mes_ano_para_ordem)

# Mostrar mensagens de status de carregamento
with st.expander("Status de carregamento dos arquivos"):
    for mes, arquivo in meses_arquivos.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            if os.path.exists(os.path.join(PROCESSED_DIR, arquivo)):
                st.success(f"{mes}: Arquivo processado encontrado")
            else:
                st.error(f"{mes}: Arquivo não encontrado")
        with col2:
            if st.button(f"Excluir {mes}", key=f"excluir_{mes}"):
                try:
                    os.remove(os.path.join(PROCESSED_DIR, arquivo))
                    st.success(f"Arquivo {mes} excluído com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir arquivo: {str(e)}")

# Widget de seleção de mês
if meses_disponiveis:
    # Gráficos de evolução (primeiro, antes dos filtros)
    st.subheader("Evolução de Vendas por Tipo de Pagamento")
    
    # Preparar dados para série temporal
    dados_serie = []
    for mes, arquivo in meses_arquivos.items():
        df_temp = carregar_processado(arquivo.replace('.parquet', ''))
        if df_temp is not None:
            df_temp = df_temp[df_temp['TIPO DE PAGAMENTO'].isin(['LISTA', 'PIX'])]
            agrupado = df_temp.groupby('TIPO DE PAGAMENTO')['VALOR'].sum().reset_index()
            for _, row in agrupado.iterrows():
                dados_serie.append({
                    'Mês': mes,
                    'TIPO DE PAGAMENTO': row['TIPO DE PAGAMENTO'],
                    'VALOR': row['VALOR']
                })
    
    if dados_serie:
        df_serie = pd.DataFrame(dados_serie)
        
        # Ordenar meses cronologicamente
        ordem_meses = {mes: i for i, mes in enumerate(meses_disponiveis)}
        df_serie['ordem'] = df_serie['Mês'].map(ordem_meses)
        df_serie = df_serie.sort_values('ordem')
        
        # Gráfico de barras para LISTA e PIX
        df_lista = df_serie[df_serie['TIPO DE PAGAMENTO'] == 'LISTA'].copy()
        df_pix = df_serie[df_serie['TIPO DE PAGAMENTO'] == 'PIX'].copy()
        
        # Criar duas colunas para os gráficos ficarem lado a lado
        col_grafico1, col_grafico2 = st.columns(2)
        
        # Gráfico de LISTA na primeira coluna
        with col_grafico1:
            if not df_lista.empty:
                df_lista['Mês'] = pd.Categorical(df_lista['Mês'], categories=meses_disponiveis, ordered=True)
                # Criar coluna de texto formatado para as barras
                df_lista['VALOR_FORMATADO'] = df_lista['VALOR'].apply(lambda x: f"R$ {x:,.0f}".replace(',', '.'))
                fig_lista = px.bar(
                    df_lista,
                    x='Mês',
                    y='VALOR',
                    title='Evolução de Vendas em Lista',
                    color_discrete_sequence=['#1f77b4'],
                    text='VALOR_FORMATADO'
                )
                fig_lista.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Valor de Vendas (R$)",
                    height=400
                )
                fig_lista.update_traces(textposition='outside')
                st.plotly_chart(fig_lista, use_container_width=True)
            else:
                st.info("Não há dados de vendas em LISTA para exibir.")
        
        # Gráfico de PIX na segunda coluna
        with col_grafico2:
            if not df_pix.empty:
                df_pix['Mês'] = pd.Categorical(df_pix['Mês'], categories=meses_disponiveis, ordered=True)
                # Criar coluna de texto formatado para as barras
                df_pix['VALOR_FORMATADO'] = df_pix['VALOR'].apply(lambda x: f"R$ {x:,.0f}".replace(',', '.'))
                fig_pix = px.bar(
                    df_pix,
                    x='Mês',
                    y='VALOR',
                    title='Evolução de Vendas em PIX',
                    color_discrete_sequence=['#2ca02c'],
                    text='VALOR_FORMATADO'
                )
                fig_pix.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Valor de Vendas (R$)",
                    height=400
                )
                fig_pix.update_traces(textposition='outside')
                st.plotly_chart(fig_pix, use_container_width=True)
            else:
                st.info("Não há dados de vendas em PIX para exibir.")
    else:
        st.warning("Não foi possível gerar as séries temporais porque não há dados suficientes.")

    # --- FILTROS GERAIS ---
    st.subheader("Filtros Gerais")
    
    # Juntar todos os dados processados para obter as opções de filtro
    all_dfs = []
    for arquivo in meses_arquivos.values():
        df_temp = carregar_processado(arquivo.replace('.parquet', ''))
        if df_temp is not None:
            all_dfs.append(df_temp)
    
    if all_dfs:
        df_all = pd.concat(all_dfs, ignore_index=True)
        
        # Layout dos filtros em colunas
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            mes_selecionado = st.selectbox("Selecione o mês", meses_disponiveis)
        
        with col_filtro2:
            # Filtro de categoria
            categorias = ['TODOS'] + sorted(df_all['TIPO DO TERMINAL'].dropna().unique().tolist())
            categoria_escolhida = st.selectbox("Categoria de Terminal", categorias, key="filtro_categoria")
        
        with col_filtro3:
            # Filtro de tipo de pagamento (dinâmico baseado na categoria)
            if categoria_escolhida == 'TODOS':
                tipos_pagamento_disponiveis = ['TODOS'] + sorted(df_all['TIPO DE PAGAMENTO'].dropna().unique().tolist())
            elif categoria_escolhida == 'POS':
                tipos_pagamento_disponiveis = ['TODOS', 'DINHEIRO', 'DÉBITO', 'PIX', 'LISTA']
            elif categoria_escolhida == 'POS SOMENTE LISTA':
                tipos_pagamento_disponiveis = ['TODOS', 'LISTA', 'PIX']
            elif categoria_escolhida == 'TOTEM DE RECARGA':
                tipos_pagamento_disponiveis = ['TODOS', 'DÉBITO', 'PIX', 'LISTA']
            else:
                # Para categorias não mapeadas, filtrar pelos tipos disponíveis nessa categoria
                df_categoria = df_all[df_all['TIPO DO TERMINAL'] == categoria_escolhida]
                tipos_pagamento_disponiveis = ['TODOS'] + sorted(df_categoria['TIPO DE PAGAMENTO'].dropna().unique().tolist())
            
            tipo_pag_escolhido = st.selectbox("Tipo de Pagamento", tipos_pagamento_disponiveis, key="filtro_tipo_pag")
        
        arquivo_selecionado = meses_arquivos[mes_selecionado]
        
        # Carregar dados do mês selecionado
        if os.path.exists(os.path.join(PROCESSED_DIR, arquivo_selecionado)):
            with st.spinner(f"Carregando dados de {mes_selecionado}..."):
                df_mes = carregar_processado(arquivo_selecionado.replace('.parquet', ''))
                if df_mes is not None:
                    # Aplicar filtros ao dataframe do mês
                    df_mes_filtrado = df_mes.copy()
                    if categoria_escolhida != 'TODOS':
                        df_mes_filtrado = df_mes_filtrado[df_mes_filtrado['TIPO DO TERMINAL'] == categoria_escolhida]
                    if tipo_pag_escolhido != 'TODOS':
                        df_mes_filtrado = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == tipo_pag_escolhido]
                    
                    # --- CARDS DINÂMICOS BASEADOS NA CATEGORIA ---
                    st.subheader(f"Métricas de Vendas - {mes_selecionado}")
                    
                    if categoria_escolhida == 'TODOS':
                        # Mostrar todos os tipos de pagamento
                        valor_total = df_mes_filtrado['VALOR'].sum()
                        valor_lista = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                        valor_pix = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                        valor_dinheiro = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'DINHEIRO']['VALOR'].sum()
                        valor_debito = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'DÉBITO']['VALOR'].sum()
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Total de Vendas", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col2:
                            st.metric("Vendas em Lista", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col3:
                            st.metric("Vendas em PIX", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col4:
                            st.metric("Vendas em Dinheiro", f"R$ {valor_dinheiro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col5:
                            st.metric("Vendas em Débito", f"R$ {valor_debito:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    elif categoria_escolhida == 'POS':
                        # POS: total geral, dinheiro, débito, pix, lista
                        valor_total = df_mes_filtrado['VALOR'].sum()
                        valor_dinheiro = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'DINHEIRO']['VALOR'].sum()
                        valor_debito = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'DÉBITO']['VALOR'].sum()
                        valor_pix = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                        valor_lista = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Total POS", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col2:
                            st.metric("Dinheiro", f"R$ {valor_dinheiro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col3:
                            st.metric("Débito", f"R$ {valor_debito:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col4:
                            st.metric("PIX", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col5:
                            st.metric("Lista", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    elif categoria_escolhida == 'POS SOMENTE LISTA':
                        # POS SOMENTE LISTA: total geral, lista, pix
                        valor_total = df_mes_filtrado['VALOR'].sum()
                        valor_lista = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                        valor_pix = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total POS Lista", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col2:
                            st.metric("Lista", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col3:
                            st.metric("PIX", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    elif categoria_escolhida == 'TOTEM DE RECARGA':
                        # TOTEM DE RECARGA: total geral, débito, pix, lista
                        valor_total = df_mes_filtrado['VALOR'].sum()
                        valor_debito = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'DÉBITO']['VALOR'].sum()
                        valor_pix = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                        valor_lista = df_mes_filtrado[df_mes_filtrado['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Totem", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col2:
                            st.metric("Débito", f"R$ {valor_debito:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col3:
                            st.metric("PIX", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        with col4:
                            st.metric("Lista", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    else:
                        # Para outras categorias, mostrar total e os tipos disponíveis
                        valor_total = df_mes_filtrado['VALOR'].sum()
                        st.metric("Total de Vendas", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    
                    # Aplicar filtros para todos os dados (para usar nos gráficos seguintes)
                    df_filtros = df_all.copy()
                    if categoria_escolhida != 'TODOS':
                        df_filtros = df_filtros[df_filtros['TIPO DO TERMINAL'] == categoria_escolhida]
                    if tipo_pag_escolhido != 'TODOS':
                        df_filtros = df_filtros[df_filtros['TIPO DE PAGAMENTO'] == tipo_pag_escolhido]

                    # --- GRÁFICO TOP 10 VENDAS POR PDV ---
                    st.subheader("Top 10 Vendas por PDV")
                    ordem_top = st.radio("Mostrar os 10 maiores ou menores?", ["Maiores", "Menores"], horizontal=True, key="top_ordem")
                    if not df_filtros.empty and 'PDV' in df_filtros.columns:
                        agrupado = df_filtros.groupby('PDV')['VALOR'].sum().reset_index()
                        agrupado = agrupado.sort_values('VALOR', ascending=(ordem_top=="Menores"))
                        top10 = agrupado.head(10)
                        fig_top = px.bar(
                            top10,
                            x='VALOR',
                            y='PDV',
                            orientation='h',
                            title=f"Top 10 {'Menores' if ordem_top=='Menores' else 'Maiores'} Vendas por PDV",
                            color='VALOR',
                            color_continuous_scale='Blues' if tipo_pag_escolhido=="LISTA" else 'Greens',
                        )
                        fig_top.update_layout(
                            xaxis_title="Valor de Vendas (R$)",
                            yaxis_title="PDV",
                            height=500
                        )
                        st.plotly_chart(fig_top, use_container_width=True)
                    else:
                        st.info("Não há dados suficientes para gerar o Top 10.")

                    # --- SÉRIE TEMPORAL POR PDV (filtrado por categoria) ---
                    st.subheader("Série Temporal de Vendas por PDV (Mês Selecionado)")

                    if 'PDV' in df_mes.columns:
                        # Filtrar PDVs baseado na categoria selecionada
                        df_mes_para_pdv = df_mes.copy()
                        if categoria_escolhida != 'TODOS':
                            df_mes_para_pdv = df_mes_para_pdv[df_mes_para_pdv['TIPO DO TERMINAL'] == categoria_escolhida]
                        
                        pdvs_filtrados = sorted(df_mes_para_pdv['PDV'].dropna().unique().tolist())
                        
                        if pdvs_filtrados:
                            pdv_escolhido = st.selectbox("Selecione o PDV para análise temporal", pdvs_filtrados, key="serie_pdv")
                            df_pdv = df_mes_para_pdv[df_mes_para_pdv['PDV'] == pdv_escolhido].copy()
                            
                            # Aplicar filtro de tipo de pagamento se selecionado
                            if tipo_pag_escolhido != 'TODOS':
                                df_pdv = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == tipo_pag_escolhido]

                            # Cards dinâmicos para o PDV específico baseados na categoria
                            valor_total = df_pdv['VALOR'].sum()
                            
                            if categoria_escolhida == 'TODOS':
                                # Mostrar todos os tipos de pagamento para TODOS
                                valor_lista = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                                valor_pix = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                                valor_dinheiro = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'DINHEIRO']['VALOR'].sum()
                                valor_debito = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'DÉBITO']['VALOR'].sum()
                                
                                col1, col2, col3, col4, col5 = st.columns(5)
                                with col1:
                                    st.metric("Total (PDV)", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col2:
                                    st.metric("Lista (PDV)", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col3:
                                    st.metric("PIX (PDV)", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col4:
                                    st.metric("Dinheiro (PDV)", f"R$ {valor_dinheiro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col5:
                                    st.metric("Débito (PDV)", f"R$ {valor_debito:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                            
                            elif categoria_escolhida == 'POS':
                                # POS: total geral, dinheiro, débito, pix, lista
                                valor_dinheiro = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'DINHEIRO']['VALOR'].sum()
                                valor_debito = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'DÉBITO']['VALOR'].sum()
                                valor_pix = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                                valor_lista = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                                
                                col1, col2, col3, col4, col5 = st.columns(5)
                                with col1:
                                    st.metric("Total POS (PDV)", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col2:
                                    st.metric("Dinheiro (PDV)", f"R$ {valor_dinheiro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col3:
                                    st.metric("Débito (PDV)", f"R$ {valor_debito:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col4:
                                    st.metric("PIX (PDV)", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col5:
                                    st.metric("Lista (PDV)", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                            
                            elif categoria_escolhida == 'POS SOMENTE LISTA':
                                # POS SOMENTE LISTA: total geral, lista, pix
                                valor_lista = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                                valor_pix = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total POS Lista (PDV)", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col2:
                                    st.metric("Lista (PDV)", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col3:
                                    st.metric("PIX (PDV)", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                            
                            elif categoria_escolhida == 'TOTEM DE RECARGA':
                                # TOTEM DE RECARGA: total geral, débito, pix, lista
                                valor_debito = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'DÉBITO']['VALOR'].sum()
                                valor_pix = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                                valor_lista = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Total Totem (PDV)", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col2:
                                    st.metric("Débito (PDV)", f"R$ {valor_debito:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col3:
                                    st.metric("PIX (PDV)", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col4:
                                    st.metric("Lista (PDV)", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                            
                            else:
                                # Para outras categorias, mostrar total e alguns tipos básicos
                                valor_lista = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                                valor_pix = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total (PDV)", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col2:
                                    st.metric("Lista (PDV)", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                                with col3:
                                    st.metric("PIX (PDV)", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                            # Gráfico de barras por dia
                            if 'DATA/HORA' in df_pdv.columns:
                                df_pdv['DATA'] = parse_dates_safely(df_pdv['DATA/HORA']).dt.date
                                agrupado = df_pdv.groupby('DATA')['VALOR'].sum().reset_index()
                                fig_pdv = px.bar(
                                    agrupado,
                                    x='DATA',
                                    y='VALOR',
                                    title=f'Evolução Diária de Vendas do PDV {pdv_escolhido} em {mes_selecionado}',
                                )
                                fig_pdv.update_layout(xaxis_title="Dia", yaxis_title="Valor de Vendas (R$)", height=400)
                                st.plotly_chart(fig_pdv, use_container_width=True)

                                # Série temporal por SERIAL
                                st.subheader("Série Temporal de Vendas por SERIAL do PDV Selecionado (Mês)")
                                if 'SERIAL' in df_pdv.columns and 'DATA/HORA' in df_pdv.columns:
                                    df_pdv['DATA'] = parse_dates_safely(df_pdv['DATA/HORA']).dt.date
                                    agrupado_serial = df_pdv.groupby(['DATA', 'SERIAL'])['VALOR'].sum().reset_index()
                                    fig_serial = px.line(
                                        agrupado_serial,
                                        x='DATA',
                                        y='VALOR',
                                        color='SERIAL',
                                        title=f'Evolução Diária de Vendas por SERIAL do PDV {pdv_escolhido} em {mes_selecionado}',
                                        markers=True
                                    )
                                    fig_serial.update_layout(xaxis_title="Dia", yaxis_title="Valor de Vendas (R$)", height=400)
                                    st.plotly_chart(fig_serial, use_container_width=True)
                                else:
                                    st.info("Coluna SERIAL não encontrada para este PDV.")
                        else:
                            st.info("Não há PDVs disponíveis para a categoria selecionada.")

                    # --- ANÁLISE COMPARATIVA QUINZENAL (vs Mês Anterior) ---
                    st.subheader("Análise Quinzenal Comparativa vs Mês Anterior")

                    if 'DATA/HORA' in df_mes_filtrado.columns:
                        df_quinz = df_mes_filtrado.copy()
                        df_quinz['DATA'] = parse_dates_safely(df_quinz['DATA/HORA']).dt.date
                        agrupado = df_quinz.groupby('DATA')['VALOR'].sum().reset_index()
                        
                        # Encontrar o mês anterior para comparação
                        mes_anterior = None
                        indice_mes_atual = meses_disponiveis.index(mes_selecionado)
                        if indice_mes_atual > 0:
                            mes_anterior = meses_disponiveis[indice_mes_atual - 1]
                            arquivo_anterior = meses_arquivos[mes_anterior]
                            
                            # Carregar dados do mês anterior
                            if os.path.exists(os.path.join(PROCESSED_DIR, arquivo_anterior)):
                                df_mes_anterior = carregar_processado(arquivo_anterior.replace('.parquet', ''))
                                
                                # Aplicar os mesmos filtros ao mês anterior
                                if categoria_escolhida != 'TODOS':
                                    df_mes_anterior = df_mes_anterior[df_mes_anterior['TIPO DO TERMINAL'] == categoria_escolhida]
                                if tipo_pag_escolhido != 'TODOS':
                                    df_mes_anterior = df_mes_anterior[df_mes_anterior['TIPO DE PAGAMENTO'] == tipo_pag_escolhido]
                                
                                # Análise quinzenal do mês anterior
                                df_quinz_anterior = df_mes_anterior.copy()
                                df_quinz_anterior['DATA'] = parse_dates_safely(df_quinz_anterior['DATA/HORA']).dt.date
                                agrupado_anterior = df_quinz_anterior.groupby('DATA')['VALOR'].sum().reset_index()
                                
                                if not agrupado_anterior.empty:
                                    agrupado_anterior['DIA'] = parse_dates_safely(agrupado_anterior['DATA']).dt.day
                                    primeira_quinzena_anterior = agrupado_anterior[agrupado_anterior['DIA'] <= 15]['VALOR'].sum()
                                    segunda_quinzena_anterior = agrupado_anterior[agrupado_anterior['DIA'] > 15]['VALOR'].sum()
                                else:
                                    primeira_quinzena_anterior = 0
                                    segunda_quinzena_anterior = 0
                            else:
                                primeira_quinzena_anterior = 0
                                segunda_quinzena_anterior = 0
                        else:
                            primeira_quinzena_anterior = 0
                            segunda_quinzena_anterior = 0
                        
                        # Comparação quinzenal atual
                        if not agrupado.empty:
                            agrupado['DIA'] = parse_dates_safely(agrupado['DATA']).dt.day
                            primeira_quinzena = agrupado[agrupado['DIA'] <= 15]['VALOR'].sum()
                            segunda_quinzena = agrupado[agrupado['DIA'] > 15]['VALOR'].sum()
                            
                            colq1, colq2 = st.columns(2)
                            with colq1:
                                # Calcular variação da 1ª quinzena vs mês anterior
                                if primeira_quinzena_anterior > 0:
                                    delta_1q = f"{((primeira_quinzena - primeira_quinzena_anterior) / primeira_quinzena_anterior * 100):+.1f}% vs {mes_anterior if mes_anterior else 'N/A'}"
                                else:
                                    delta_1q = "Novo" if primeira_quinzena > 0 else ""
                                
                                st.metric(
                                    label="1ª Quinzena",
                                    value=f"R$ {primeira_quinzena:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                                    delta=delta_1q
                                )
                            with colq2:
                                # Calcular variação da 2ª quinzena vs mês anterior
                                if segunda_quinzena_anterior > 0:
                                    delta_2q = f"{((segunda_quinzena - segunda_quinzena_anterior) / segunda_quinzena_anterior * 100):+.1f}% vs {mes_anterior if mes_anterior else 'N/A'}"
                                else:
                                    delta_2q = "Novo" if segunda_quinzena > 0 else ""
                                
                                st.metric(
                                    label="2ª Quinzena",
                                    value=f"R$ {segunda_quinzena:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                                    delta=delta_2q
                                )
                        
                        # Gráfico quinzenal
                        if tipo_pag_escolhido != "TODOS":
                            tipo_label = tipo_pag_escolhido
                        else:
                            tipo_label = "TODOS os Tipos"
                        fig_quinz = px.bar(
                            agrupado,
                            x='DATA',
                            y='VALOR',
                            title=f'Evolução Diária de Vendas ({tipo_label}) - {mes_selecionado}',
                            color_discrete_sequence=['#1f77b4'] if tipo_pag_escolhido == 'LISTA' else ['#2ca02c']
                        )
                        fig_quinz.update_layout(xaxis_title="Dia", yaxis_title="Valor de Vendas (R$)", height=400)
                        st.plotly_chart(fig_quinz, use_container_width=True)
                    else:
                        st.info("Não há dados suficientes para análise quinzenal neste mês.")
                else:
                    st.error(f"Não foi possível carregar os dados para {mes_selecionado}.")
        else:
            st.error(f"Não foi possível carregar os dados para {mes_selecionado} porque o arquivo não existe.")
    else:
        st.warning("Não há dados disponíveis para análise.")
else:
    st.warning("Não há arquivos processados. Por favor, faça o upload de um arquivo CSV seguindo o padrão 'mês_ano.csv' (ex: janeiro_25.csv)")

# Rodapé
st.markdown("---")
st.caption("Dashboard de Vendas © 2025 - Desenvolvido por João Pedro Mendes") 