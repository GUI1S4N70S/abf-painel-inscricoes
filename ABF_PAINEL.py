import streamlit as st
import pandas as pd
import numpy as np
import os

# ==========================================
# CONFIGURAÇÃO DO LAYOUT (FRONT-END)
# ==========================================
st.set_page_config(page_title="ABF - Painel de Dados de Inscrições", page_icon="📊", layout="wide")

st.title("📊 ABF - Painel de Dados de Inscrições")
st.markdown("Faça o upload das planilhas diárias abaixo. O sistema identificará os dados novos, removerá as duplicatas e atualizará a base para o Power BI.")

st.divider()

# Botão de Upload de arquivos (permite anexar várias planilhas de uma vez)
arquivos_anexados = st.file_uploader(
    "Arraste e solte as planilhas Excel atualizadas aqui", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if arquivos_anexados:
    if st.button("🚀 Processar e Atualizar Base Power BI", type="primary"):
        with st.spinner('Processando e cruzando dados...'):
            
            # 1. Leitura e Empilhamento das planilhas anexadas
            lista_dfs = []
            for arquivo in arquivos_anexados:
                df_temp = pd.read_excel(arquivo, sheet_name='Sef Inscritos')
                lista_dfs.append(df_temp)
            
            df_novo = pd.concat(lista_dfs, ignore_index=True)

            # 2. Se já existir uma base anterior, junta com a nova para não perder histórico
            caminho_base_final = 'Base_PowerBI_Tratada.xlsx'
            if os.path.exists(caminho_base_final):
                df_antigo = pd.read_excel(caminho_base_final)
                df_geral = pd.concat([df_antigo, df_novo], ignore_index=True)
            else:
                df_geral = df_novo

            # 3. Remoção de Duplicatas (Mantém sempre a atualização mais recente do mesmo ID)
            df = df_geral.drop_duplicates(subset=['Id'], keep='last').copy()

            # Converter colunas de data
            df['Data de início da inscrição'] = pd.to_datetime(df['Data de início da inscrição'])
            df['Data de finalização da inscrição'] = pd.to_datetime(df['Data de finalização da inscrição'])

            # ==========================================
            # TRATAMENTO DE DADOS (REGRAS DE NEGÓCIO)
            # ==========================================
            
            # PONTO 1: Regra do Ano do Evento (+1)
            df['Ano do Evento'] = df['Data de início da inscrição'].dt.year + 1

            # PONTO 2: Dia Relativo de Inscrição
            datas_inicio_campanha = {
                2026: pd.to_datetime('2025-08-01'),
                2027: pd.to_datetime('2026-08-03')
            }

            def calcular_dia_relativo(row):
                ano_evento = row['Ano do Evento']
                data_inscricao = row['Data de início da inscrição']
                if pd.notnull(data_inscricao) and ano_evento in datas_inicio_campanha:
                    data_base = datas_inicio_campanha[ano_evento]
                    return (data_inscricao - data_base).days + 1
                return np.nan

            df['Dia de Inscrição'] = df.apply(calcular_dia_relativo, axis=1)

            # PONTO 3: Mês de Início
            df['Mês Início'] = df['Data de início da inscrição'].dt.month

            # PONTO 5 (CORRIGIDO): Status Geral x Etapa Específica
            # A coluna "Etapa em que está" permanece INTACTA com "Dados Básicos", "Pagamento", etc.
            # Criamos apenas essa coluna para facilitar a contagem total de finalizadas no Power BI
            df['Status Geral PBI'] = np.where(
                df['Etapa em que está'] == 'Confirmação', 
                'Finalizada', 
                'Iniciada'
            )

            # ==========================================
            # SALVAR BASE PARA O POWER BI
            # ==========================================
            df.to_excel(caminho_base_final, index=False)
            
            st.success("✅ Base de dados atualizada com sucesso! O arquivo 'Base_PowerBI_Tratada.xlsx' já está pronto para o Power BI.")
            st.metric(label="Total de Inscrições Únicas Processadas", value=len(df))