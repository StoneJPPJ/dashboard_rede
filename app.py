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

if meses_disponiveis:
    # Preparar dados para série temporal - Evolução de Vendas
    # Esse código precisa vir antes dos filtros pois não depende deles
    st.subheader("Evolução de Vendas por Tipo de Pagamento")
    
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
    
    # --- FILTROS GERAIS PARA TODO O DASHBOARD --- (Movido para depois dos gráficos de evolução)
    st.subheader("Filtros Gerais")
    
    # Widget de seleção de mês
    mes_selecionado = st.selectbox("Selecione o mês", meses_disponiveis)
    arquivo_selecionado = meses_arquivos[mes_selecionado]
    
    # Criar uma lista de todos os tipos de pagamento disponíveis
    tipos_pagamento_disponiveis = ['TODOS']
    categorias_disponiveis = ['TODOS']
    
    # Juntar todos os dados para obter os valores únicos
    df_todos = []
    for arquivo in meses_arquivos.values():
        df_temp = carregar_processado(arquivo.replace('.parquet', ''))
        if df_temp is not None:
            df_todos.append(df_temp)
    
    if df_todos:
        df_todos = pd.concat(df_todos, ignore_index=True)
        # Adicionar tipos de pagamento disponíveis
        tipos_pagamento_disponiveis.extend(sorted(df_todos['TIPO DE PAGAMENTO'].dropna().unique().tolist()))
        # Adicionar categorias disponíveis
        if 'TIPO DO TERMINAL' in df_todos.columns:
            categorias_disponiveis.extend(sorted(df_todos['TIPO DO TERMINAL'].dropna().unique().tolist()))
    
    # Colunas para os filtros
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        tipo_pagamento_selecionado = st.selectbox(
            "Tipo de Pagamento", 
            tipos_pagamento_disponiveis,
            key="filtro_geral_tipo_pagamento"
        )
    
    with col_filtro2:
        categoria_selecionada = st.selectbox(
            "Categoria de Equipamento", 
            categorias_disponiveis,
            key="filtro_geral_categoria"
        )
    
    # Carregar dados do mês selecionado
    if os.path.exists(os.path.join(PROCESSED_DIR, arquivo_selecionado)):
        with st.spinner(f"Carregando dados de {mes_selecionado}..."):
            df_mes = carregar_processado(arquivo_selecionado.replace('.parquet', ''))
            if df_mes is not None:
                # Layout em colunas para os cards (movido para estar abaixo dos filtros)
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
                
                # --- SÉRIE TEMPORAL QUINZENAL (Mês Selecionado) ---
                st.subheader("Série Temporal Quinzenal (Mês Selecionado)")

                # Aplicar filtros gerais ao dataframe do mês
                df_quinz = df_mes.copy()
                if tipo_pagamento_selecionado != 'TODOS':
                    df_quinz = df_quinz[df_quinz['TIPO DE PAGAMENTO'] == tipo_pagamento_selecionado]
                
                if categoria_selecionada != 'TODOS' and 'TIPO DO TERMINAL' in df_quinz.columns:
                    df_quinz = df_quinz[df_quinz['TIPO DO TERMINAL'] == categoria_selecionada]

                if 'DATA/HORA' in df_quinz.columns:
                    df_quinz['DATA'] = pd.to_datetime(df_quinz['DATA/HORA'], errors='coerce').dt.date
                    agrupado = df_quinz.groupby('DATA')['VALOR'].sum().reset_index()
                    
                    # Determinar a cor do gráfico com base no tipo de pagamento
                    cor_grafico = 'Blues'  # Padrão
                    if tipo_pagamento_selecionado == 'PIX':
                        cor_grafico = 'Greens'
                    elif tipo_pagamento_selecionado == 'LISTA':
                        cor_grafico = 'Blues'
                    elif tipo_pagamento_selecionado == 'DINHEIRO':
                        cor_grafico = 'Reds'
                    elif tipo_pagamento_selecionado == 'DÉBITO':
                        cor_grafico = 'Purples'
                    
                    # Determinar a cor específica com base no tipo de pagamento
                    cor_especifica = '#1f77b4'  # Azul (padrão para LISTA)
                    if tipo_pagamento_selecionado == 'PIX':
                        cor_especifica = '#2ca02c'  # Verde
                    elif tipo_pagamento_selecionado == 'DINHEIRO':
                        cor_especifica = '#d62728'  # Vermelho
                    elif tipo_pagamento_selecionado == 'DÉBITO':
                        cor_especifica = '#9467bd'  # Roxo
                    
                    # Comparação quinzenal com o mês anterior
                    # Obter quinzenas do mês atual
                    agrupado['DIA'] = pd.to_datetime(agrupado['DATA']).dt.day
                    primeira_quinzena_atual = agrupado[agrupado['DIA'] <= 15]['VALOR'].sum()
                    segunda_quinzena_atual = agrupado[agrupado['DIA'] > 15]['VALOR'].sum()
                    
                    # Encontrar o mês anterior
                    if meses_disponiveis:
                        indice_mes_atual = meses_disponiveis.index(mes_selecionado)
                        mes_anterior = None
                        if indice_mes_atual > 0:
                            mes_anterior = meses_disponiveis[indice_mes_atual - 1]
                        
                        # Calcular valores do mês anterior se disponível
                        primeira_quinzena_anterior = 0
                        segunda_quinzena_anterior = 0
                        
                        if mes_anterior:
                            arquivo_mes_anterior = meses_arquivos[mes_anterior]
                            df_mes_anterior = carregar_processado(arquivo_mes_anterior.replace('.parquet', ''))
                            
                            if df_mes_anterior is not None:
                                # Aplicar os mesmos filtros
                                if tipo_pagamento_selecionado != 'TODOS':
                                    df_mes_anterior = df_mes_anterior[df_mes_anterior['TIPO DE PAGAMENTO'] == tipo_pagamento_selecionado]
                                
                                if categoria_selecionada != 'TODOS' and 'TIPO DO TERMINAL' in df_mes_anterior.columns:
                                    df_mes_anterior = df_mes_anterior[df_mes_anterior['TIPO DO TERMINAL'] == categoria_selecionada]
                                
                                if 'DATA/HORA' in df_mes_anterior.columns:
                                    df_mes_anterior['DATA'] = pd.to_datetime(df_mes_anterior['DATA/HORA'], errors='coerce').dt.date
                                    agrupado_anterior = df_mes_anterior.groupby('DATA')['VALOR'].sum().reset_index()
                                    agrupado_anterior['DIA'] = pd.to_datetime(agrupado_anterior['DATA']).dt.day
                                    primeira_quinzena_anterior = agrupado_anterior[agrupado_anterior['DIA'] <= 15]['VALOR'].sum()
                                    segunda_quinzena_anterior = agrupado_anterior[agrupado_anterior['DIA'] > 15]['VALOR'].sum()
                        
                        # Mostrar comparações quinzenais antes do gráfico
                        st.write(f"### Comparação Quinzenal: {mes_selecionado}")
                        col_comp1, col_comp2 = st.columns(2)
                        
                        with col_comp1:
                            st.metric(
                                label=f"1ª Quinzena",
                                value=f"R$ {primeira_quinzena_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                                delta=f"{((primeira_quinzena_atual-primeira_quinzena_anterior)/primeira_quinzena_anterior*100):+.1f}% vs mês anterior" if primeira_quinzena_anterior > 0 else None
                            )
                            
                            if primeira_quinzena_anterior > 0:
                                st.caption(f"Mês anterior ({mes_anterior}): R$ {primeira_quinzena_anterior:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        
                        with col_comp2:
                            st.metric(
                                label=f"2ª Quinzena",
                                value=f"R$ {segunda_quinzena_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                                delta=f"{((segunda_quinzena_atual-segunda_quinzena_anterior)/segunda_quinzena_anterior*100):+.1f}% vs mês anterior" if segunda_quinzena_anterior > 0 else None
                            )
                            
                            if segunda_quinzena_anterior > 0:
                                st.caption(f"Mês anterior ({mes_anterior}): R$ {segunda_quinzena_anterior:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        
                        # Comparação entre as quinzenas do mês atual
                        if primeira_quinzena_atual > segunda_quinzena_atual:
                            st.success(f"⬆️ **A 1ª quinzena teve mais vendas!** Diferença: R$ {(primeira_quinzena_atual-segunda_quinzena_atual):,.2f}")
                        elif segunda_quinzena_atual > primeira_quinzena_atual:
                            st.info(f"⬆️ **A 2ª quinzena teve mais vendas!** Diferença: R$ {(segunda_quinzena_atual-primeira_quinzena_atual):,.2f}")
                        else:
                            st.warning("🔵 **As duas quinzenas tiveram o mesmo valor de vendas!**")
                    
                    # Gráfico
                    fig_quinz = px.bar(
                        agrupado,
                        x='DATA',
                        y='VALOR',
                        title=f'Evolução Diária de Vendas em {mes_selecionado}',
                        color_discrete_sequence=[cor_especifica]
                    )
                    fig_quinz.update_layout(xaxis_title="Dia", yaxis_title="Valor de Vendas (R$)", height=400)
                    st.plotly_chart(fig_quinz, use_container_width=True)
                else:
                    st.info("Não há dados de data/hora para análise quinzenal.")

                # --- GRÁFICO TOP 10 VENDAS POR PDV COM FILTROS GERAIS ---
                st.subheader("Top 10 Vendas por PDV")
                ordem_top = st.radio("Mostrar os 10 maiores ou menores?", ["Maiores", "Menores"], horizontal=True, key="top_ordem")
                
                # Juntar todos os dados dos meses para o top 10
                df_top = []
                for arquivo in meses_arquivos.values():
                    df_temp = carregar_processado(arquivo.replace('.parquet', ''))
                    if df_temp is not None:
                        df_top.append(df_temp)
                if df_top:
                    df_top = pd.concat(df_top, ignore_index=True)
                    
                    # Aplicar filtros gerais
                    if tipo_pagamento_selecionado != 'TODOS':
                        df_top = df_top[df_top['TIPO DE PAGAMENTO'] == tipo_pagamento_selecionado]
                    
                    if categoria_selecionada != 'TODOS' and 'TIPO DO TERMINAL' in df_top.columns:
                        df_top = df_top[df_top['TIPO DO TERMINAL'] == categoria_selecionada]
                    
                    if 'PDV' in df_top.columns:
                        agrupado = df_top.groupby('PDV')['VALOR'].sum().reset_index()
                        agrupado = agrupado.sort_values('VALOR', ascending=(ordem_top=="Menores"))
                        top10 = agrupado.head(10)
                        
                        # Determinar a cor do gráfico com base no tipo de pagamento
                        cor_grafico = 'Blues'  # Padrão
                        if tipo_pagamento_selecionado == 'PIX':
                            cor_grafico = 'Greens'
                        elif tipo_pagamento_selecionado == 'LISTA':
                            cor_grafico = 'Blues'
                        elif tipo_pagamento_selecionado == 'DINHEIRO':
                            cor_grafico = 'Reds'
                        elif tipo_pagamento_selecionado == 'DÉBITO':
                            cor_grafico = 'Purples'
                        
                        fig_top = px.bar(
                            top10,
                            x='VALOR',
                            y='PDV',
                            orientation='h',
                            title=f"Top 10 {'Menores' if ordem_top=='Menores' else 'Maiores'} Vendas por PDV",
                            color='VALOR',
                            color_continuous_scale=cor_grafico,
                        )
                        fig_top.update_layout(
                            xaxis_title="Valor de Vendas (R$)",
                            yaxis_title="PDV",
                            height=500
                        )
                        st.plotly_chart(fig_top, use_container_width=True)
                    else:
                        st.warning("Coluna 'PDV' não encontrada nos arquivos.")
                else:
                    st.info("Não há dados suficientes para gerar o Top 10.")
                
                # --- SÉRIE TEMPORAL POR PDV (apenas para o mês selecionado) COM FILTROS GERAIS ---
                st.subheader("Série Temporal de Vendas por PDV (Mês Selecionado)")

                if 'PDV' in df_mes.columns:
                    pdvs = sorted(df_mes['PDV'].dropna().unique().tolist())
                    pdv_escolhido = st.selectbox("Selecione o PDV para análise temporal", pdvs, key="serie_pdv")
                    df_pdv = df_mes[df_mes['PDV'] == pdv_escolhido].copy()
                    
                    # Aplicar filtros gerais ao dataframe do PDV
                    if tipo_pagamento_selecionado != 'TODOS':
                        df_pdv = df_pdv[df_pdv['TIPO DE PAGAMENTO'] == tipo_pagamento_selecionado]
                    
                    if categoria_selecionada != 'TODOS' and 'TIPO DO TERMINAL' in df_pdv.columns:
                        df_pdv = df_pdv[df_pdv['TIPO DO TERMINAL'] == categoria_selecionada]

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

            else:
                st.error(f"Não foi possível carregar os dados para {mes_selecionado}.")
    else:
        st.error(f"Não foi possível carregar os dados para {mes_selecionado} porque o arquivo não existe.")
else:
    st.warning("Não há arquivos processados. Por favor, faça o upload de um arquivo CSV seguindo o padrão 'mês_ano.csv' (ex: janeiro_25.csv)")

# Rodapé
st.markdown("---")
st.caption("Dashboard de Vendas © 2025 - Desenvolvido por João Pedro Mendes") 