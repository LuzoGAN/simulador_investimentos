import flet as ft
from datetime import date, timedelta
import pandas as pd
from decimal import Decimal


# Função para obter a taxa Selic anual mais recente
def recente_selic_anual():
    url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados?formato=csv'
    selic = pd.read_csv(url, sep=';')
    selic['data'] = pd.to_datetime(selic['data'], format='%d/%m/%Y')
    selic['valor'] = selic['valor'].str.replace(',', '.').astype(float)
    recente_selic_anual = selic.sort_values(by='data', ascending=False).iloc[0]['valor']
    return recente_selic_anual


# Carrega o DataFrame com informações de investimentos
metricas_info = pd.read_excel(r'metricas_investimento.xlsx')


# Função para calcular o valor futuro do investimento
def valor_futuro(taxa, n_periodos, pagamento, valor_presente):
    try:
        return valor_presente * (1 + taxa) ** n_periodos + pagamento * (((1 + taxa) ** n_periodos - 1) / taxa)
    except ZeroDivisionError:
        return 0


# Função para determinar a alíquota de imposto de renda com base no prazo
def aliquota_imposto(prazo_dias):
    if prazo_dias < 181:
        return Decimal('0.225')  # 22,5% de imposto
    elif prazo_dias < 361:
        return Decimal('0.20')  # 20% de imposto
    elif prazo_dias < 721:
        return Decimal('0.175')  # 17,5% de imposto
    else:
        return Decimal('0.15')  # 15% de imposto


def main(page: ft.Page):
    page.title = "Simulador de Investimentos - Sicoob"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Configura o tema e as cores principais do Sicoob
    sicoob_primary = "#005c5a"
    sicoob_secondary = "#9dcbba"

    page.theme = ft.Theme(
        primary_color=sicoob_primary,
        #accent_color=sicoob_secondary,
    )

    # Informações da data atual
    data_hoje = date.today()
    hoje = ft.Text(
        f'Data Atual: {data_hoje.strftime("%d/%m/%Y")}',
        size=16,
        weight=ft.FontWeight.BOLD,
        color=sicoob_primary
    )

    # Funções de seleção de investimento e prazo
    def dropdown_invest(e):
        selected_invest = dd_invest.value
        prazo_unicos = metricas_info[metricas_info['Investimento'] == selected_invest]['Prazo'].unique()
        dd_prazo.options = [ft.dropdown.Option(str(prazo)) for prazo in prazo_unicos]
        page.update()

    def dropdown_prazo(e):
        dias_extraido = metricas_info['Prazo'].str.extract(r'(\d+)')[0]
        metricas_info['Dias'] = pd.to_numeric(dias_extraido, errors='coerce').fillna(0).astype(int)
        selected_prazo = int(dd_prazo.value.split()[0])
        prazo_final = data_hoje + timedelta(days=selected_prazo)
        t_data_final.value = f"Data final do investimento: {prazo_final.strftime('%d/%m/%Y')}"
        page.update()

    # Função para capturar o valor de investimento
    def valor_(e):
        v.value = e.control.value
        page.update()

    # Função para calcular a simulação
    def calcular_investimento():
        invest = dd_invest.value
        prazo = dd_prazo.value
        busca = invest + prazo + 'sim'
        try:
            valor_l = metricas_info.loc[metricas_info['&1'] == busca, 'CDI'].values[0]
            return valor_l
        except:
            return "Investimento Inválido"

    def calcular(e):
        try:
            taxa = Decimal(calcular_investimento()) * Decimal(recente_selic_anual()) / 100
            n_periodos = Decimal(dd_prazo.value.split()[0]) / 365
            pagamento = 0
            valor_presente = Decimal(valor.value)
            vf = valor_futuro(taxa, n_periodos, pagamento, valor_presente)
            valor_bruto = vf - valor_presente
            prazo_dias = int(dd_prazo.value.split()[0])
            aliquota = aliquota_imposto(prazo_dias)
            valor_liquido = valor_bruto * (1 - aliquota)
            r.value = (
                f"Simulação Completa:\n\n"
                f"Valor Futuro: R$ {vf:.2f}\n"
                f"Valor Bruto: R$ {valor_bruto:.2f}\n"
                f"Valor Líquido: R$ {valor_liquido:.2f}\n"
                f"Alíquota de IR: {aliquota * 100}%"
            )
        except Exception as ex:
            r.value = f"Erro no cálculo: {ex}"
        page.update()

    # Componentes do layout
    dd_invest = ft.Dropdown(
        label="Escolha o Investimento",
        on_change=dropdown_invest,
        options=[ft.dropdown.Option(invest) for invest in metricas_info['Investimento'].unique()],
        width=250,
        filled=True
    )

    dd_prazo = ft.Dropdown(
        label="Prazo (dias)",
        width=250,
        on_change=dropdown_prazo,
        filled=True
    )

    valor = ft.TextField(
        label='Valor a Investir (R$)',
        on_change=valor_,
        width=250,
        text_align=ft.TextAlign.CENTER,
        filled=True
    )

    btn_calcular = ft.ElevatedButton(
        "Calcular Simulação",
        on_click=calcular,
        width=200,
        color=ft.colors.WHITE,
        bgcolor=sicoob_primary,
    )

    t_data_final = ft.Text()
    r = ft.Text(size=16, color=sicoob_secondary, weight=ft.FontWeight.BOLD)

    # Organizar todos os componentes centralizados na tela
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    hoje,
                    dd_invest,
                    dd_prazo,
                    t_data_final,
                    valor,
                    btn_calcular,
                    r
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.alignment.center,
            padding=20,
            width=500,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.GREY_300),
        )
    )


ft.app(main)
