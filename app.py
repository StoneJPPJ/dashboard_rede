import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
import shutil
import calendar

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
                df = pd.read_csv(
                    arquivo,
                    encoding=encoding,
                    sep=';',
                    on_bad_lines='skip',
                    skipinitialspace=True,
                    skip_blank_lines=True,
                    dtype={'VALOR PAGO': str}
                )
                if 'VALOR PAGO' in df.columns:
                    df = df.rename(columns={'VALOR PAGO': 'VALOR'})
                if 'VALOR' in df.columns:
                    df['VALOR'] = df['VALOR'].astype(str).str.replace(r'[^\d.,]', '', regex=True)
                    df['VALOR'] = df['VALOR'].str.replace(',', '.')
                    df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                    df = df.dropna(subset=['VALOR'])
                    df = df[df['VALOR'] >= 0]
                if 'TIPO DE PAGAMENTO' in df.columns:
                    df['TIPO DE PAGAMENTO'] = df['TIPO DE PAGAMENTO'].astype(str).str.strip().str.upper()
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
    mes_selecionado = st.selectbox("Selecione o mês", meses_disponiveis)
    arquivo_selecionado = meses_arquivos[mes_selecionado]
    
    # Carregar dados do mês selecionado
    if os.path.exists(os.path.join(PROCESSED_DIR, arquivo_selecionado)):
        with st.spinner(f"Carregando dados de {mes_selecionado}..."):
            df_mes = carregar_processado(arquivo_selecionado.replace('.parquet', ''))
            if df_mes is not None:
                # Layout em colunas para os cards
                col1, col2, col3 = st.columns(3)
                
                # Calcular valores totais
                valor_total = df_mes['VALOR'].sum()
                valor_lista = df_mes[df_mes['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                valor_pix = df_mes[df_mes['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                
                # Card 1: Total
                with col1:
                    st.metric(
                        label="Total de Vendas",
                        value=f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    )
                
                # Card 2: Lista
                with col2:
                    st.metric(
                        label="Vendas em Lista",
                        value=f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    )
                
                # Card 3: PIX
                with col3:
                    st.metric(
                        label="Vendas em PIX",
                        value=f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    )
                
                # Gráficos de evolução
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
                    
                    # Gráfico de barras para LISTA
                    df_lista = df_serie[df_serie['TIPO DE PAGAMENTO'] == 'LISTA'].copy()
                    df_pix = df_serie[df_serie['TIPO DE PAGAMENTO'] == 'PIX'].copy()
                    
                    # Garantir que o eixo X está na ordem correta
                    if not df_lista.empty:
                        df_lista['Mês'] = pd.Categorical(df_lista['Mês'], categories=meses_disponiveis, ordered=True)
                        fig_lista = px.bar(
                            df_lista,
                            x='Mês',
                            y='VALOR',
                            title='Evolução de Vendas em Lista',
                            color_discrete_sequence=['#1f77b4']
                        )
                        fig_lista.update_layout(
                            xaxis_title="Mês",
                            yaxis_title="Valor de Vendas (R$)",
                            height=400
                        )
                        st.plotly_chart(fig_lista, use_container_width=True)
                    else:
                        st.info("Não há dados de vendas em LISTA para exibir.")
                    
                    if not df_pix.empty:
                        df_pix['Mês'] = pd.Categorical(df_pix['Mês'], categories=meses_disponiveis, ordered=True)
                        fig_pix = px.bar(
                            df_pix,
                            x='Mês',
                            y='VALOR',
                            title='Evolução de Vendas em PIX',
                            color_discrete_sequence=['#2ca02c']
                        )
                        fig_pix.update_layout(
                            xaxis_title="Mês",
                            yaxis_title="Valor de Vendas (R$)",
                            height=400
                        )
                        st.plotly_chart(fig_pix, use_container_width=True)
                    else:
                        st.info("Não há dados de vendas em PIX para exibir.")
                else:
                    st.warning("Não foi possível gerar as séries temporais porque não há dados suficientes.")

                # --- FILTROS GERAIS PARA OS GRÁFICOS ---
                st.subheader("Filtros Gerais para Análise")

                # Juntar todos os dados processados para obter as opções de filtro
                all_dfs = []
                for arquivo in meses_arquivos.values():
                    df_temp = carregar_processado(arquivo.replace('.parquet', ''))
                    if df_temp is not None:
                        all_dfs.append(df_temp)
                if all_dfs:
                    df_all = pd.concat(all_dfs, ignore_index=True)
                    # Filtro de categoria
                    categorias = ['Todos'] + sorted(df_all['TIPO DO TERMINAL'].dropna().unique().tolist())
                    categoria_escolhida = st.selectbox("Categoria (TIPO DO TERMINAL)", categorias, key="filtro_categoria")
                    # Filtro de tipo de pagamento
                    tipos_pagamento = ['Todos'] + sorted(df_all['TIPO DE PAGAMENTO'].dropna().unique().tolist())
                    tipo_pag_escolhido = st.selectbox("Tipo de Pagamento", tipos_pagamento, key="filtro_tipo_pag")
                    # Aplicar filtros
                    df_filtros = df_all.copy()
                    if categoria_escolhida != 'Todos':
                        df_filtros = df_filtros[df_filtros['TIPO DO TERMINAL'] == categoria_escolhida]
                    if tipo_pag_escolhido != 'Todos':
                        df_filtros = df_filtros[df_filtros['TIPO DE PAGAMENTO'] == tipo_pag_escolhido]
                else:
                    df_filtros = pd.DataFrame()

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

                # --- SÉRIE TEMPORAL POR PDV (apenas para o mês selecionado)
                st.subheader("Série Temporal de Vendas por PDV (Mês Selecionado)")

                if 'PDV' in df_mes.columns:
                    pdvs = sorted(df_mes['PDV'].dropna().unique().tolist())
                    pdv_escolhido = st.selectbox("Selecione o PDV para análise temporal", pdvs, key="serie_pdv")
                    df_pdv = df_mes[df_mes['PDV'] == pdv_escolhido].copy()

                    # Cards
                    valor_total = df_pdv['VALOR'].sum()
                    valor_lista = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'LISTA']['VALOR'].sum()
                    valor_pix = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == 'PIX']['VALOR'].sum()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Vendas (PDV)", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    with col2:
                        st.metric("Vendas em Lista (PDV)", f"R$ {valor_lista:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    with col3:
                        st.metric("Vendas em PIX (PDV)", f"R$ {valor_pix:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                    # Gráfico de barras por dia (ou por DATA/HORA, se quiser granularidade)
                    if 'DATA/HORA' in df_pdv.columns:
                        df_pdv['DATA'] = pd.to_datetime(df_pdv['DATA/HORA'], errors='coerce').dt.date
                        agrupado = df_pdv.groupby('DATA')['VALOR'].sum().reset_index()
                        fig_pdv = px.bar(
                            agrupado,
                            x='DATA',
                            y='VALOR',
                            title=f'Evolução Diária de Vendas do PDV {pdv_escolhido} em {mes_selecionado}',
                        )
                        fig_pdv.update_layout(xaxis_title="Dia", yaxis_title="Valor de Vendas (R$)", height=400)
                        st.plotly_chart(fig_pdv, use_container_width=True)

                    # Série temporal por SERIAL (no mês selecionado)
                    st.subheader("Série Temporal de Vendas por SERIAL do PDV Selecionado (Mês)")
                    if 'SERIAL' in df_pdv.columns and 'DATA/HORA' in df_pdv.columns:
                        df_pdv['DATA'] = pd.to_datetime(df_pdv['DATA/HORA'], errors='coerce').dt.date
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

                # --- SÉRIE TEMPORAL QUINZENAL POR TIPO DE PAGAMENTO (usando os filtros gerais) ---
                st.subheader("Série Temporal Quinzenal por Tipo de Pagamento (Mês Selecionado)")

                if not df_filtros.empty and 'DATA/HORA' in df_filtros.columns:
                    df_quinz = df_filtros.copy()
                    df_quinz['DATA'] = pd.to_datetime(df_quinz['DATA/HORA'], errors='coerce').dt.date
                    agrupado = df_quinz.groupby('DATA')['VALOR'].sum().reset_index()
                    # Comparação quinzenal
                    if not agrupado.empty:
                        agrupado['DIA'] = pd.to_datetime(agrupado['DATA']).dt.day
                        primeira_quinzena = agrupado[agrupado['DIA'] <= 15]['VALOR'].sum()
                        segunda_quinzena = agrupado[agrupado['DIA'] > 15]['VALOR'].sum()
                        colq1, colq2 = st.columns(2)
                        with colq1:
                            st.metric(
                                label="1ª Quinzena",
                                value=f"R$ {primeira_quinzena:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                                delta=f"{((primeira_quinzena-segunda_quinzena)/segunda_quinzena*100):+.1f}%" if segunda_quinzena else ""
                            )
                        with colq2:
                            st.metric(
                                label="2ª Quinzena",
                                value=f"R$ {segunda_quinzena:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                                delta=f"{((segunda_quinzena-primeira_quinzena)/primeira_quinzena*100):+.1f}%" if primeira_quinzena else ""
                            )
                    # Corrigir f-string do título
                    if tipo_pag_escolhido != "Todos":
                        tipo_label = tipo_pag_escolhido
                    else:
                        tipo_label = "Todos os Tipos"
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
    st.warning("Não há arquivos processados. Por favor, faça o upload de um arquivo CSV seguindo o padrão 'mês_ano.csv' (ex: janeiro_25.csv)")

# Rodapé
st.markdown("---")
st.caption("Dashboard de Vendas © 2023 - Desenvolvido com Streamlit e Python") 