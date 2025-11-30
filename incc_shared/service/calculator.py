import json
import os
from datetime import date
from decimal import Decimal
from typing import Optional

import boto3
from dateutil.relativedelta import relativedelta

from incc_shared.exceptions.errors import InvalidState

BUCKET = os.environ["STORAGE_BUCKET"]
KEY = "incc-index/history.json"
MAX_PARCELAS = 420


incc_cache = None


def formata_data_indice(raw_date: date):
    return raw_date.strftime("%d/%m/%Y")


def get_incc_list():
    global incc_cache

    if incc_cache is not None:
        return incc_cache

    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=BUCKET, Key=KEY)
    content = response["Body"].read().decode("utf-8")
    incc_cache = json.loads(content)
    return incc_cache


def get_incc_map():
    return {i["data"]: i["valor"] for i in get_incc_list()}


def calcula_reajuste(valor: Decimal, data_inicio: date):
    lista_incc = get_incc_map()
    data_atual = data_inicio.replace(day=1)
    resultado = {
        "data_inicio": data_inicio,
        "valor_original": valor,
        "reajustes": [
            {
                "data_parcela": data_inicio,
                "data_incc": None,
                "incc": None,
                "valor": valor,
            }
        ],
    }
    ultima_parcela = valor
    for i in range(MAX_PARCELAS):
        data_indice = formata_data_indice(data_atual)
        try:
            incc = Decimal(lista_incc[data_indice])
            parcela = round(ultima_parcela * (1 + incc / 100), 2)
            resultado["reajustes"].append(
                {
                    "data_parcela": data_inicio + relativedelta(months=i + 1),
                    "data_incc": data_atual,
                    "incc": incc,
                    "valor": parcela,
                }
            )
            ultima_parcela = parcela
            data_atual += relativedelta(months=1)
        except KeyError:
            break
    else:
        raise InvalidState("Limite de calculo atingido")
    return resultado


def calcula_valor(valor: Decimal, data_inicio: date, data_fim: Optional[date] = None):
    data_atual = data_inicio.replace(day=1)
    data_fim = data_fim.replace(day=1) if data_fim else None
    lista_incc = get_incc_map()
    resultado = valor
    for _ in range(MAX_PARCELAS):
        if data_fim and data_atual >= data_fim:
            break

        data_indice = formata_data_indice(data_atual)
        try:
            incc = Decimal(lista_incc[data_indice])
            resultado = resultado * (1 + incc / 100)
        except KeyError as e:
            print(f"Data {e} não existe")
            break
        data_atual += relativedelta(months=1)
    else:
        raise InvalidState("Limite de calculo atingido")

    return round(resultado, 2)
