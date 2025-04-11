import streamlit as st
import pandas as pd
import numpy as np
import logging
import os

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Iniciando o aplicativo Streamlit")

# Configuração da página
st.title("Gestão de Metas")
logger.debug("Título renderizado")

# Menu com abas
tab1, tab2, tab3 = st.tabs(["Metas Distribuição", "Meta Hospitalar", "Meta Redes"])

# Regionais por aba
regionais_distribuicao = ["MG / RJ / ES", "SP", "NORDESTE", "COE / NORTE", "SUL"]
regionais_hospitalar = ["HOSPITALAR"]
regionais_redes = ["REDES"]

# Função para processar os dados
def processar_dados(clientes_file, produtos_file, metas_regionais, filtro_regiao):
    try:
        logger.debug("Lendo tabelas")
        if use_last_files:
            clientes = pd.read_excel(clientes_file)
            produtos = pd.read_excel(produtos_file)
        else:
            clientes = pd.read_excel(clientes_file)
            produtos = pd.read_excel(produtos_file)
        logger.debug("Tabelas lidas com sucesso")

        # Mantém as colunas desejadas + peso
        colunas_clientes = ['COD SAP', 'DESCRIÇÃO CLIENTE', 'RCA / GC', 'GERENTE', 'REGIÃO', 'peso']
        colunas_produtos = ['SAP', 'DESCRIÇÃO', 'peso']

        # Verifica se as colunas necessárias existem
        if not all(col in clientes.columns for col in colunas_clientes):
            st.error("A tabela de clientes deve conter: COD SAP, DESCRIÇÃO CLIENTE, RCA / GC, GERENTE, REGIÃO, peso")
            raise ValueError("Colunas faltando na tabela de clientes")
        if not all(col in produtos.columns for col in colunas_produtos):
            st.error("A tabela de produtos deve conter: SAP, DESCRIÇÃO, peso")
            raise ValueError("Colunas faltando na tabela de produtos")

        clientes = clientes[colunas_clientes]
        produtos = produtos[colunas_produtos]

        # Filtra pela região específica
        clientes = clientes[clientes['REGIÃO'].isin(filtro_regiao)]

        # Renomeia as colunas
        clientes = clientes.rename(columns={
            'COD SAP': 'Código cliente',
            'DESCRIÇÃO CLIENTE': 'Nome cliente',
            'RCA / GC': 'RCA',
            'GERENTE': 'GERENTE',
            'REGIÃO': 'REGIÃO',
            'peso': 'Peso Cliente'
        })
        produtos = produtos.rename(columns={
            'SAP': 'Código produto',
            'DESCRIÇÃO': 'Nome produto',
            'peso': 'Peso Produto'
        })

        # Normaliza os pesos dos clientes por regional (soma = 100%)
        clientes['Peso Cliente Normalizado'] = clientes.groupby('REGIÃO')['Peso Cliente'].transform(lambda x: x / x.sum())

        # Produto cartesiano
        logger.debug("Criando produto cartesiano")
        tabela_final = pd.merge(clientes.assign(key=1), produtos.assign(key=1), on='key').drop('key', axis=1)

        # Calcula Meta Cliente Total
        tabela_final['Meta Cliente Total'] = tabela_final.apply(
            lambda row: metas_regionais.get(row['REGIÃO'], 0) * row['Peso Cliente Normalizado'], axis=1
        )

        # Calcula Meta Cliente Produto
        tabela_final['Peso Produto Normalizado'] = tabela_final['Peso Produto'] / tabela_final.groupby('Código cliente')['Peso Produto'].transform('sum')
        tabela_final['Meta Cliente Produto'] = tabela_final['Meta Cliente Total'] * tabela_final['Peso Produto Normalizado']

        # Seleciona apenas as colunas desejadas para exibição
        colunas_exibir = ['Código cliente', 'Nome cliente', 'RCA', 'GERENTE', 'REGIÃO', 'Código produto', 'Nome produto', 'Meta Cliente Produto']
        tabela_final = tabela_final[colunas_exibir]

        return tabela_final

    except Exception as e:
        st.error(f"Erro ao processar: {str(e)}")
        logger.error(f"Erro: {str(e)}")
        return None

# Aba 1: Metas Distribuição
with tab1:
    # Entrada da meta geral
    meta_geral_dist = st.number_input("Digite a Meta Geral (Distribuição)", min_value=0.0, step=1000.0, format="%.2f", key="meta_dist")
    logger.debug(f"Meta geral distribuição: {meta_geral_dist}")

    # Metas regionais
    metas_regionais_dist = {}
    st.subheader("Metas por Regional (Distribuição)")
    for regional in regionais_distribuicao:
        metas_regionais_dist[regional] = st.number_input(f"Meta {regional}", min_value=0.0, step=1000.0, format="%.2f", key=f"dist_{regional}")
        logger.debug(f"Meta {regional} (Dist): {metas_regionais_dist[regional]}")

    # Validação
    soma_metas_dist = sum(metas_regionais_dist.values())
    if soma_metas_dist > 0 and abs(soma_metas_dist - meta_geral_dist) > 0.01:
        st.error(f"A soma das metas regionais ({soma_metas_dist:,.2f}) não corresponde à meta geral ({meta_geral_dist:,.2f})")

    # Upload
    use_last_files = st.checkbox("Usar últimos arquivos utilizados", value=False, key="use_dist")
    if use_last_files:
        clientes_path = r"C:\Users\alan.mendes\Desktop\Python\base clientes.xlsx"
        produtos_path = r"C:\Users\alan.mendes\Desktop\Python\base produtos.xlsx"
        if os.path.exists(clientes_path) and os.path.exists(produtos_path):
            st.write(f"Usando arquivo de clientes: {clientes_path}")
            st.write(f"Usando arquivo de produtos: {produtos_path}")
            clientes_file = clientes_path
            produtos_file = produtos_path
        else:
            st.error("Arquivos fixos não encontrados.")
            clientes_file = None
            produtos_file = None
    else:
        clientes_file = st.file_uploader("Insira a Tabela de Clientes (Excel)", type=['xlsx', 'xlsm'], key="clientes_dist")
        produtos_file = st.file_uploader("Insira a Tabela de Produtos (Excel)", type=['xlsx', 'xlsm'], key="produtos_dist")

    if st.button("Processar Distribuição", key="btn_dist"):
        if clientes_file and produtos_file:
            tabela_final = processar_dados(clientes_file, produtos_file, metas_regionais_dist, regionais_distribuicao)
            if tabela_final is not None:
                st.subheader("Resultado Distribuição")
                st.dataframe(tabela_final)
                excel_buffer = pd.ExcelWriter('resultado_distribuicao.xlsx', engine='openpyxl')
                tabela_final.to_excel(excel_buffer, index=False)
                excel_buffer.close()
                with open('resultado_distribuicao.xlsx', 'rb') as f:
                    st.download_button(
                        label="Download Resultado Distribuição",
                        data=f,
                        file_name="resultado_distribuicao.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

# Aba 2: Meta Hospitalar
with tab2:
    # Entrada da meta geral
    meta_geral_hosp = st.number_input("Digite a Meta Geral (Hospitalar)", min_value=0.0, step=1000.0, format="%.2f", key="meta_hosp")
    logger.debug(f"Meta geral hospitalar: {meta_geral_hosp}")

    # Metas regionais
    metas_regionais_hosp = {}
    st.subheader("Meta Hospitalar")
    for regional in regionais_hospitalar:
        metas_regionais_hosp[regional] = st.number_input(f"Meta {regional}", min_value=0.0, step=1000.0, format="%.2f", key=f"hosp_{regional}")
        logger.debug(f"Meta {regional} (Hosp): {metas_regionais_hosp[regional]}")

    # Validação
    soma_metas_hosp = sum(metas_regionais_hosp.values())
    if soma_metas_hosp > 0 and abs(soma_metas_hosp - meta_geral_hosp) > 0.01:
        st.error(f"A soma das metas regionais ({soma_metas_hosp:,.2f}) não corresponde à meta geral ({meta_geral_hosp:,.2f})")

    # Upload
    use_last_files = st.checkbox("Usar últimos arquivos utilizados", value=False, key="use_hosp")
    if use_last_files:
        clientes_path = r"C:\Users\alan.mendes\Desktop\Python\base clientes.xlsx"
        produtos_path = r"C:\Users\alan.mendes\Desktop\Python\base produtos.xlsx"
        if os.path.exists(clientes_path) and os.path.exists(produtos_path):
            st.write(f"Usando arquivo de clientes: {clientes_path}")
            st.write(f"Usando arquivo de produtos: {produtos_path}")
            clientes_file = clientes_path
            produtos_file = produtos_path
        else:
            st.error("Arquivos fixos não encontrados.")
            clientes_file = None
            produtos_file = None
    else:
        clientes_file = st.file_uploader("Insira a Tabela de Clientes (Excel)", type=['xlsx', 'xlsm'], key="clientes_hosp")
        produtos_file = st.file_uploader("Insira a Tabela de Produtos (Excel)", type=['xlsx', 'xlsm'], key="produtos_hosp")

    if st.button("Processar Hospitalar", key="btn_hosp"):
        if clientes_file and produtos_file:
            tabela_final = processar_dados(clientes_file, produtos_file, metas_regionais_hosp, regionais_hospitalar)
            if tabela_final is not None:
                st.subheader("Resultado Hospitalar")
                st.dataframe(tabela_final)
                excel_buffer = pd.ExcelWriter('resultado_hospitalar.xlsx', engine='openpyxl')
                tabela_final.to_excel(excel_buffer, index=False)
                excel_buffer.close()
                with open('resultado_hospitalar.xlsx', 'rb') as f:
                    st.download_button(
                        label="Download Resultado Hospitalar",
                        data=f,
                        file_name="resultado_hospitalar.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

# Aba 3: Meta Redes
with tab3:
    # Entrada da meta geral
    meta_geral_redes = st.number_input("Digite a Meta Geral (Redes)", min_value=0.0, step=1000.0, format="%.2f", key="meta_redes")
    logger.debug(f"Meta geral redes: {meta_geral_redes}")

    # Metas regionais
    metas_regionais_redes = {}
    st.subheader("Meta Redes")
    for regional in regionais_redes:
        metas_regionais_redes[regional] = st.number_input(f"Meta {regional}", min_value=0.0, step=1000.0, format="%.2f", key=f"redes_{regional}")
        logger.debug(f"Meta {regional} (Redes): {metas_regionais_redes[regional]}")

    # Validação
    soma_metas_redes = sum(metas_regionais_redes.values())
    if soma_metas_redes > 0 and abs(soma_metas_redes - meta_geral_redes) > 0.01:
        st.error(f"A soma das metas regionais ({soma_metas_redes:,.2f}) não corresponde à meta geral ({meta_geral_redes:,.2f})")

    # Upload
    use_last_files = st.checkbox("Usar últimos arquivos utilizados", value=False, key="use_redes")
    if use_last_files:
        clientes_path = r"C:\Users\alan.mendes\Desktop\Python\base clientes.xlsx"
        produtos_path = r"C:\Users\alan.mendes\Desktop\Python\base produtos.xlsx"
        if os.path.exists(clientes_path) and os.path.exists(produtos_path):
            st.write(f"Usando arquivo de clientes: {clientes_path}")
            st.write(f"Usando arquivo de produtos: {produtos_path}")
            clientes_file = clientes_path
            produtos_file = produtos_path
        else:
            st.error("Arquivos fixos não encontrados.")
            clientes_file = None
            produtos_file = None
    else:
        clientes_file = st.file_uploader("Insira a Tabela de Clientes (Excel)", type=['xlsx', 'xlsm'], key="clientes_redes")
        produtos_file = st.file_uploader("Insira a Tabela de Produtos (Excel)", type=['xlsx', 'xlsm'], key="produtos_redes")

    if st.button("Processar Redes", key="btn_redes"):
        if clientes_file and produtos_file:
            tabela_final = processar_dados(clientes_file, produtos_file, metas_regionais_redes, regionais_redes)
            if tabela_final is not None:
                st.subheader("Resultado Redes")
                st.dataframe(tabela_final)
                excel_buffer = pd.ExcelWriter('resultado_redes.xlsx', engine='openpyxl')
                tabela_final.to_excel(excel_buffer, index=False)
                excel_buffer.close()
                with open('resultado_redes.xlsx', 'rb') as f:
                    st.download_button(
                        label="Download Resultado Redes",
                        data=f,
                        file_name="resultado_redes.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

# Instruções
st.sidebar.title("Instruções")
st.sidebar.write("""
1. Escolha a aba desejada (Distribuição, Hospitalar ou Redes).
2. Insira a meta geral para a aba selecionada.
3. Insira as metas por regional (devem somar a meta geral).
4. Escolha usar os últimos arquivos ou faça upload das tabelas.
5. Clique em 'Processar'.
6. Veja o resultado e baixe o arquivo.
""")
logger.debug("Instruções renderizadas")