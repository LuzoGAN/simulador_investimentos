import flet as ft
from datetime import date, timedelta
import pandas as pd
from decimal import Decimal

def recente_selic_anual():
    url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados?formato=csv'
    selic = pd.read_csv(url, sep=';')
    selic['data'] = pd.to_datetime(selic['data'], format='%d/%m/%Y')
    selic['valor'] = selic['valor'].str.replace(',', '.').astype(float)
    recente_selic_anual = selic.sort_values(by='data', ascending=False).iloc[0]['valor']
    return recente_selic_anual

# Carrega o DataFrame com informações de investimentos
metricas_info = pd.read_excel(r'metricas_investimento.xlsx')

def valor_futuro(taxa, n_periodos, pagamento, valor_presente):
    """Calcula o valor futuro do investimento."""
    try:
        return valor_presente * (1 + taxa) ** n_periodos + pagamento * (((1 + taxa) ** n_periodos - 1) / taxa)
    except ZeroDivisionError:
        return 0

def aliquota_imposto(prazo_dias):
    """Calcula a alíquota de imposto de renda com base no prazo do investimento."""
    if prazo_dias < 181:
        return Decimal('0.225')  # 22,5% de imposto
    elif prazo_dias < 361:
        return Decimal('0.20')   # 20% de imposto
    elif prazo_dias < 721:
        return Decimal('0.175')  # 17,5% de imposto
    else:
        return Decimal('0.15')   # 15% de imposto

def main(page: ft.Page):
    t = ft.Text()
    data_hoje = date.today()
    hoje = ft.Text(f'Dia atual: {data_hoje.strftime("%d/%m/%Y")}')

    # Função de dropdown para selecionar o investimento
    def dropdown_invest(e):
        selected_invest = dd_invest.value
        prazo_unicos = metricas_info[metricas_info['Investimento'] == selected_invest]['Prazo'].unique()
        dd_prazo.options = [ft.dropdown.Option(str(prazo)) for prazo in prazo_unicos]
        page.update()

    # Função para capturar o prazo e calcular a data final
    def dropdown_prazo(e):
        dias_extraido = metricas_info['Prazo'].str.extract(r'(\d+)')[0]
        metricas_info['Dias'] = pd.to_numeric(dias_extraido, errors='coerce').fillna(0).astype(int)

        selected_prazo = int(dd_prazo.value.split()[0])
        prazo_final = data_hoje + timedelta(days=selected_prazo)
        t.value = f"Data final: {prazo_final.strftime('%d/%m/%Y')}"
        page.update()

    # Função para capturar o valor numérico do campo de valor investido
    def valor_(e):
        v.value = e.control.value
        page.update()

    v = ft.Text()

    # Campo para inserção do valor a ser investido
    valor = ft.TextField(
        label='Valor a Investir',
        on_change=valor_,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$", replacement_string="")
    )

    # Função para capturar a taxa do investimento
    def calcular_investimento():
        invest = dd_invest.value
        prazo = dd_prazo.value
        busca = invest + prazo + 'sim'
        try:
            valor_l = metricas_info.loc[metricas_info['&1'] == busca, 'CDI'].values[0]
            return valor_l
        except:
            return "Investimento Inválido"

    # Função principal para calcular o valor futuro e rendimento líquido
    def calcular(e):
        try:
            # Taxa obtida do investimento selecionado e Selic anual
            taxa = Decimal(calcular_investimento()) * Decimal(recente_selic_anual()) / 100
            n_periodos = Decimal(dd_prazo.value.split()[0]) / 365
            pagamento = 0  # Sem pagamentos periódicos
            valor_presente = Decimal(valor.value)

            # Calcula o valor futuro do investimento
            vf = valor_futuro(taxa, n_periodos, pagamento, valor_presente)

            # Calcula o valor bruto (quanto o investidor ganharia sem impostos)
            valor_bruto = vf - valor_presente

            # Cálculo da alíquota do imposto com base no prazo
            prazo_dias = int(dd_prazo.value.split()[0])
            aliquota = aliquota_imposto(prazo_dias)

            # Cálculo do valor líquido após imposto
            valor_liquido = valor_bruto * (1 - aliquota)

            # Exibe o resultado final
            r.value = f"Resultado Final:\nValor Futuro: R$ {vf:.2f}\nValor Bruto: R$ {valor_bruto:.2f}\nValor Líquido: R$ {valor_liquido:.2f} (alíquota: {aliquota * 100}%)"
        except Exception as ex:
            r.value = f"Erro no cálculo: {ex}"

        page.update()

    # Dropdowns e botão para interação
    dd_invest = ft.Dropdown(
        on_change=dropdown_invest,
        options=[ft.dropdown.Option(invest) for invest in metricas_info['Investimento'].unique()],
        width=200
    )

    dd_prazo = ft.Dropdown(width=200, on_change=dropdown_prazo)

    btn_calcular = ft.ElevatedButton("Calcular", on_click=calcular)

    r = ft.Text()

    # Adiciona os elementos na página
    page.add(hoje, dd_invest, dd_prazo, t, valor, v, btn_calcular, r)

ft.app(main)
