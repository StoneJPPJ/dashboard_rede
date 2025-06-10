# 📊 Dashboard de Vendas

Este projeto é um dashboard interativo para análise de vendas, desenvolvido em Python com Streamlit e Plotly. Ele permite ao usuário fazer upload de arquivos CSV, visualizar gráficos dinâmicos e obter insights sobre as vendas de forma simples e intuitiva.

## 🚀 Como usar

1. **Acesse o dashboard** (link do Streamlit Cloud será fornecido após o deploy).
2. **Faça upload dos arquivos CSV** que deseja analisar (um ou vários arquivos).
3. **Visualize os gráficos e métricas** automaticamente gerados.
4. **Remova arquivos** se desejar, usando a interface.
5. **Os dados não ficam salvos** após fechar ou reiniciar o app (privacidade garantida).

## 📂 Padrão dos arquivos CSV
- O nome do arquivo deve seguir o padrão: `mes_ano.csv` (exemplo: `janeiro_25.csv`, `marco_25.csv`).
- O arquivo deve conter, no mínimo, as colunas:
  - `T.PGTO` (Tipo de Pagamento)
  - `V.PAGO` (Valor Pago)
  - `PDV` (Ponto de Venda)
  - `EQUIPAMENTO` (Tipo do Terminal)
  - `DATA/HORA`
  - `SERIAL`
- O separador deve ser ponto e vírgula (`;`).
- Os valores podem conter vírgula ou ponto como separador decimal.

## 🖥️ Funcionalidades
- Upload e exclusão de arquivos CSV pela interface.
- Gráficos de evolução mensal de vendas por tipo de pagamento (LISTA/PIX).
- Gráfico Top 10 PDVs por vendas, com filtro por categoria.
- Análise detalhada por PDV e por SERIAL.
- Comparação visual entre primeira e segunda quinzena do mês.
- Cards com valores totais, por LISTA e por PIX.

## ⚠️ Observações importantes
- **Privacidade:** Os dados enviados não ficam salvos após fechar ou reiniciar o app.
- **Limite de upload:** O tamanho máximo de cada arquivo pode variar conforme o ambiente do Streamlit Cloud (em geral, até 200MB).
- **Requisitos:**
  - Python 3.8+
  - Bibliotecas: streamlit, pandas, plotly, matplotlib
- **Deploy:**
  - O deploy pode ser feito facilmente no [Streamlit Cloud](https://streamlit.io/cloud) conectando este repositório.

## 📦 Instalação local (opcional)
Se quiser rodar localmente:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 👨‍💻 Contribuição
Pull requests são bem-vindos! Sinta-se à vontade para sugerir melhorias ou novas funcionalidades.

---
Dashboard de Vendas © 2023 - Desenvolvido com Streamlit e Python 