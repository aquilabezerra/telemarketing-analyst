
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import os

# ====== Tema do Seaborn ======
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)


# ====== Função para ler dados ======
@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except Exception:
        return pd.read_excel(file_data)


# ====== Função para filtros ======
@st.cache_data
def multiselect_filter(df, col, selecionados):
    if 'all' in selecionados:
        return df
    else:
        return df[df[col].isin(selecionados)].reset_index(drop=True)


# ====== Converter DataFrame para CSV ======
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


# ====== Converter DataFrame para Excel ======
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data


# ====== Função principal ======
def main():
    # Configuração da página
    st.set_page_config(
        page_title='Telemarketing Analysis',
        page_icon='📞',
        layout="wide",
        initial_sidebar_state='expanded'
    )

    st.write('# Telemarketing Analysis')
    st.markdown("---")

    # ====== Sidebar ======
    if os.path.exists("Bank-Branding.jpg"):
        image = Image.open("Bank-Branding.jpg")
        st.sidebar.image(image)
    else:
        st.sidebar.info("🔎 Imagem 'Bank-Branding.jpg' não encontrada.")

    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type=['csv', 'xlsx'])

    if data_file_1 is not None:
        bank_raw = load_data(data_file_1)
        bank = bank_raw.copy()

        st.write('## Antes dos filtros')
        st.write(bank_raw.head())

        # ====== Formulário de filtros ======
        with st.sidebar.form(key='my_form'):
            graph_type = st.radio('Tipo de gráfico:', ('Barras', 'Pizza'))

            max_age = int(bank.age.max())
            min_age = int(bank.age.min())
            idades = st.slider(
                label='Idade',
                min_value=min_age,
                max_value=max_age,
                value=(min_age, max_age),
                step=1
            )

            def add_all_option(lst):
                lst = sorted(lst)
                lst.append('all')
                return lst

            jobs_selected = st.multiselect("Profissão", add_all_option(bank.job.unique().tolist()), ['all'])
            marital_selected = st.multiselect("Estado civil", add_all_option(bank.marital.unique().tolist()), ['all'])
            default_selected = st.multiselect("Default", add_all_option(bank.default.unique().tolist()), ['all'])
            housing_selected = st.multiselect("Tem financiamento imob?", add_all_option(bank.housing.unique().tolist()), ['all'])
            loan_selected = st.multiselect("Tem empréstimo?", add_all_option(bank.loan.unique().tolist()), ['all'])
            contact_selected = st.multiselect("Meio de contato", add_all_option(bank.contact.unique().tolist()), ['all'])
            month_selected = st.multiselect("Mês do contato", add_all_option(bank.month.unique().tolist()), ['all'])
            day_of_week_selected = st.multiselect("Dia da semana", add_all_option(bank.day_of_week.unique().tolist()), ['all'])

            submit_button = st.form_submit_button(label='Aplicar')

        # ====== Aplicar filtros ======
        bank = (
            bank.query("age >= @idades[0] and age <= @idades[1]")
            .pipe(multiselect_filter, 'job', jobs_selected)
            .pipe(multiselect_filter, 'marital', marital_selected)
            .pipe(multiselect_filter, 'default', default_selected)
            .pipe(multiselect_filter, 'housing', housing_selected)
            .pipe(multiselect_filter, 'loan', loan_selected)
            .pipe(multiselect_filter, 'contact', contact_selected)
            .pipe(multiselect_filter, 'month', month_selected)
            .pipe(multiselect_filter, 'day_of_week', day_of_week_selected)
        )

        # ====== Dados filtrados ======
        st.write('## Após os filtros')
        st.write(bank.head())

        df_xlsx = to_excel(bank)
        st.download_button(
            label='📥 Download tabela filtrada em EXCEL',
            data=df_xlsx,
            file_name='bank_filtered.xlsx'
        )

        st.markdown("---")

        # ====== Proporção do target ======
        bank_raw_target_perc = bank_raw.y.value_counts(normalize=True).to_frame() * 100
        bank_raw_target_perc = bank_raw_target_perc.sort_index()
        bank_raw_target_perc.columns = ['y']

        try:
            bank_target_perc = bank.y.value_counts(normalize=True).to_frame() * 100
            bank_target_perc = bank_target_perc.sort_index()
            bank_target_perc.columns = ['y']
        except Exception:
            st.error('Erro no filtro dos dados.')

        # ====== Exibir tabelas lado a lado ======
        col1, col2 = st.columns(2)

        df_xlsx = to_excel(bank_raw_target_perc)
        col1.write('### Proporção original')
        col1.write(bank_raw_target_perc)
        col1.download_button(
            label='📥 Download',
            data=df_xlsx,
            file_name='bank_raw_y.xlsx'
        )

        df_xlsx = to_excel(bank_target_perc)
        col2.write('### Proporção da tabela com filtros')
        col2.write(bank_target_perc)
        col2.download_button(
            label='📥 Download',
            data=df_xlsx,
            file_name='bank_y.xlsx'
        )

        st.markdown("---")

        st.write('## Proporção de aceite')

        # ====== PLOTS ======
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))

        if graph_type == 'Barras':
            sns.barplot(x=bank_raw_target_perc.index, y='y', data=bank_raw_target_perc, ax=ax[0])
            ax[0].bar_label(ax[0].containers[0])
            ax[0].set_title('Dados brutos', fontweight="bold")

            sns.barplot(x=bank_target_perc.index, y='y', data=bank_target_perc, ax=ax[1])
            ax[1].bar_label(ax[1].containers[0])
            ax[1].set_title('Dados filtrados', fontweight="bold")

        else:
            bank_raw_target_perc.plot(kind='pie', autopct='%.2f%%', y='y', ax=ax[0])
            ax[0].set_title('Dados brutos', fontweight="bold")

            bank_target_perc.plot(kind='pie', autopct='%.2f%%', y='y', ax=ax[1])
            ax[1].set_title('Dados filtrados', fontweight="bold")

        st.pyplot(fig)


# ====== Rodar app ======
if __name__ == '__main__':
    main()
    











