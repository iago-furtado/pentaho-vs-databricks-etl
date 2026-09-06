# Resultados Comparativos do Experimento ETL: Pentaho e Databricks

## 1. Objetivo deste resumo

Este documento consolida os resultados medidos para servir de insumo à redação do artigo de MBA. Ele compara duas implementações da mesma lógica de negócio: leitura de clientes, produtos e transações; limpeza do nome do cliente; junção pelas chaves `customer_id` e `product_id`; cálculo do valor total da transação; e agregação por ano, mês, estado e categoria de produto.

Os resultados devem ser apresentados como observações dos ambientes utilizados. Eles não sustentam uma afirmação universal de superioridade entre plataformas, porque o Pentaho foi executado localmente e o Databricks em infraestrutura Serverless gerenciada.

## 2. Implementações avaliadas

| Plataforma | Bronze para Silver | Silver para Gold | Armazenamento Silver/Gold |
| --- | --- | --- | --- |
| Databricks | Notebook PySpark: leitura dos CSVs, limpeza, joins, campos derivados e escrita | Notebook PySpark: agregação mensal por estado e categoria | Tabelas Delta gerenciadas no Unity Catalog |
| Pentaho Data Integration 9.4 | `01_bronze_to_silver_sales_transactions.ktr` | `02_silver_to_gold_monthly_sales.ktr` | Arquivos CSV locais em `pentaho/output/<scenario>/` |

No Databricks, os notebooks foram executados no Databricks Free Edition com Serverless compute. A disponibilidade de um SQL Warehouse `2X-Small` é uma limitação da edição gratuita, mas não define uma configuração fixa de CPU, memória ou workers para os notebooks Serverless.

### 2.1 Ambiente local do Pentaho

As transformações Pentaho foram executadas localmente no Spoon, com a seguinte configuração registrada após os testes:

| Componente | Especificação |
| --- | --- |
| Notebook | Dell G3 3500 |
| Processador | Intel Core i5-10300H @ 2,50 GHz (4 núcleos / 8 processadores lógicos) |
| Memória RAM | 8 GB |
| Armazenamento | SSD NVMe ADATA de 512 GB |
| Sistema operacional | Windows 11 Home 64-bit, build 26200 |
| Pentaho Data Integration | 9.4.0.0-343 |
| Java disponível no ambiente | Java 21.0.6 LTS, 64-bit |

Essa especificação descreve o ambiente local observado; ela não representa uma configuração de referência para todas as implantações do Pentaho.

## 3. Cenários e validação de dados

| Cenário | Clientes | Produtos | Transações | Total de vendas validado |
| --- | ---: | ---: | ---: | ---: |
| 100k | 10.000 | 2.000 | 100.000 | BRL 292.908.411,46 |
| 500k | 50.000 | 10.000 | 500.000 | BRL 1.493.576.980,67 |
| 1m | 100.000 | 20.000 | 1.000.000 | BRL 2.987.230.578,70 |
| 5m | 500.000 | 100.000 | 5.000.000 | BRL 14.942.606.763,93 |

Os datasets foram gerados deterministicamente com a seed `20260827`. Para todos os cenários e ambas as plataformas, a soma de `transaction_count` na Gold e a soma de vendas corresponderam aos valores esperados. A Gold teve menos linhas físicas porque agrupa por ano, mês, estado e categoria.

## 4. Método de medição

- Em cada cenário e camada, foi executado um warm-up antes das três execuções medidas; os warm-ups foram excluídos das estatísticas.
- No Databricks, o tempo foi medido dentro dos notebooks, incluindo leitura, transformação e escrita da tabela Delta; a validação ocorreu após o encerramento da cronometragem.
- No Pentaho, o tempo foi obtido a partir dos timestamps `Dispatching started` e `The transformation has finished!!` do Spoon. Portanto, a resolução dos tempos do Pentaho é de um segundo.
- Os tempos end-to-end apresentados são a soma das médias Bronze-to-Silver e Silver-to-Gold. A geração de CSV/PDF de entrega no Databricks não integra o benchmark.
- Os warm-ups do Pentaho foram executados antes das séries, mas seus horários não foram registrados sistematicamente no arquivo de resultados; somente as execuções medidas estão registradas.

## 5. Resultados principais

Tempos em segundos; cada média é calculada a partir de três execuções medidas.

| Cenário | Databricks Bronze-Silver | Databricks Silver-Gold | Databricks end-to-end | Pentaho Bronze-Silver | Pentaho Silver-Gold | Pentaho end-to-end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100k | 2,731 | 2,062 | 4,793 | 1,667 | 2,000 | 3,667 |
| 500k | 3,791 | 2,042 | 5,833 | 5,667 | 8,000 | 13,667 |
| 1m | 4,577 | 1,972 | 6,549 | 9,000 | 25,333 | 34,333 |
| 5m | 6,566 | 2,129 | 8,695 | 50,000 | 124,333 | 174,333 |

### 5.1 Variabilidade das execuções medidas

Desvio-padrão amostral, em segundos.

| Cenário | Databricks Bronze-Silver | Databricks Silver-Gold | Pentaho Bronze-Silver | Pentaho Silver-Gold |
| --- | ---: | ---: | ---: | ---: |
| 100k | 0,473 | 0,302 | 0,577 | 0,000 |
| 500k | 0,252 | 0,116 | 2,082 | 1,732 |
| 1m | 0,011 | 0,078 | 0,000 | 4,726 |
| 5m | 0,812 | 0,072 | 5,292 | 13,868 |

## 6. Interpretação adequada dos resultados

1. Nos ambientes observados, o Databricks apresentou crescimento moderado do tempo end-to-end entre 100k e 5m transações (de 4,793 s para 8,695 s). A etapa Silver-to-Gold permaneceu próxima de dois segundos nos quatro cenários.
2. No Pentaho local, o aumento de volume afetou especialmente a etapa Silver-to-Gold. Essa etapa precisa ordenar e agregar arquivos CSV localmente; a média passou de 2,000 s em 100k para 124,333 s em 5m.
3. Em 100k, as diferenças são pequenas e a resolução de um segundo do Spoon limita qualquer interpretação fina. A diferença de comportamento torna-se mais visível a partir de 500k.
4. A comparação deve considerar que o Databricks escreveu tabelas Delta gerenciadas e o Pentaho escreveu CSVs locais. Esse é um aspecto físico e arquitetural específico de cada plataforma, não uma variável completamente controlada.
5. A infraestrutura também não é equivalente: Databricks Serverless é gerenciado e dinâmico, enquanto o Pentaho usa recursos da máquina local. Assim, a conclusão apropriada é sobre o desempenho medido nessas condições, e não sobre todas as implantações possíveis das ferramentas.

## 7. Texto-base sugerido para a seção de resultados do artigo

> Foram avaliadas implementações equivalentes de ETL em Databricks e Pentaho Data Integration, usando quatro volumes de dados sintéticos determinísticos, de 100 mil a 5 milhões de transações. Em todos os cenários, ambas as implementações preservaram a contagem de transações e o valor agregado das vendas. No ambiente Databricks Free Edition com compute Serverless, o tempo médio end-to-end variou de 4,793 s (100k) a 8,695 s (5m). No ambiente Pentaho local, os tempos médios variaram de 3,667 s a 174,333 s. O crescimento no Pentaho foi concentrado sobretudo na agregação Silver-to-Gold, que envolve ordenação e agrupamento de arquivos CSV no ambiente local. Os resultados devem ser interpretados como observações das configurações avaliadas, pois as plataformas utilizaram infraestruturas e formatos físicos de saída distintos.

## 8. Registros de origem

- Execuções individuais: `results/experiment_runs.csv`.
- Resultado detalhado do Databricks: `docs/databricks-experiment-results.md`.
- Transformações Pentaho: `pentaho/transformations/`.
- Saídas locais do Pentaho: `pentaho/output/<scenario>/` (ignoradas pelo Git).
