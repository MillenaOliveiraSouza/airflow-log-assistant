# Resultados da avaliação

Modo: **somente busca (sem LLM)**

| Conjunto | Logs | Acerto top-1 | Causa certa entre as 3 primeiras |
| --- | --- | --- | --- |
| Desenvolvimento | 25 | 25/25 (100%) | 25/25 (100%) |
| Holdout (nunca usado para ajustes) | 8 | 6/8 (75%) | 7/8 (88%) |

## Desenvolvimento

| Log | Dificuldade | Esperado | Previsto | Top-1 | Top-3 | Pontuação | Confiança |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01_oom_carga_vendas | easy | oom_sigkill | oom_sigkill | ✓ | ✓ | 0.58 | media |
| 02_timeout_query | easy | execution_timeout | execution_timeout | ✓ | ✓ | 0.85 | alta |
| 03_conexao_inexistente | easy | connection_not_defined | connection_not_defined | ✓ | ✓ | 0.91 | alta |
| 04_variable_ausente | easy | variable_not_found | variable_not_found | ✓ | ✓ | 0.82 | alta |
| 05_dag_quebrada | easy | dag_import_error | dag_import_error | ✓ | ✓ | 0.88 | alta |
| 06_permissao_bigquery | easy | gcp_permission_denied | gcp_permission_denied | ✓ | ✓ | 0.89 | alta |
| 07_tabela_inexistente | easy | bq_table_not_found | bq_table_not_found | ✓ | ✓ | 0.74 | alta |
| 08_esquema_bigquery | easy | bq_schema_mismatch | bq_schema_mismatch | ✓ | ✓ | 0.75 | alta |
| 09_arquivo_gcs | easy | gcs_object_not_found | gcs_object_not_found | ✓ | ✓ | 0.93 | alta |
| 10_upstream | easy | upstream_failed | upstream_failed | ✓ | ✓ | 0.93 | alta |
| 11_sensor | easy | sensor_timeout | sensor_timeout | ✓ | ✓ | 0.88 | alta |
| 12_pool | easy | pool_no_slots | pool_no_slots | ✓ | ✓ | 0.77 | alta |
| 13_xcom | easy | xcom_serialization | xcom_serialization | ✓ | ✓ | 0.78 | alta |
| 14_rate_limit | easy | api_rate_limit | api_rate_limit | ✓ | ✓ | 0.79 | alta |
| 15_banco_recusou | easy | db_connection_refused | db_connection_refused | ✓ | ✓ | 0.88 | alta |
| 16_jinja | easy | jinja_template_error | jinja_template_error | ✓ | ✓ | 0.84 | alta |
| 17_coluna_pandas | easy | dataframe_missing_column | dataframe_missing_column | ✓ | ✓ | 0.58 | media |
| 18_zumbi | easy | zombie_task | zombie_task | ✓ | ✓ | 0.59 | media |
| 19_gcs_mas_permissao | hard | gcp_permission_denied | gcp_permission_denied | ✓ | ✓ | 0.92 | alta |
| 20_pod_oomkilled | hard | oom_sigkill | oom_sigkill | ✓ | ✓ | 0.44 | baixa |
| 21_timeout_api_externa | hard | execution_timeout | execution_timeout | ✓ | ✓ | 0.83 | alta |
| 22_esquema_novo_campo | hard | bq_schema_mismatch | bq_schema_mismatch | ✓ | ✓ | 0.66 | media |
| 23_encoding | hard | desconhecido | desconhecido | ✓ | ✓ | 0.12 | baixa |
| 24_permissao_arquivo_local | hard | desconhecido | desconhecido | ✓ | ✓ | 0.38 | baixa |
| 25_divisao_zero | hard | desconhecido | desconhecido | ✓ | ✓ | 0.10 | baixa |

## Holdout (nunca usado para ajustes)

| Log | Dificuldade | Esperado | Previsto | Top-1 | Top-3 | Pontuação | Confiança |
| --- | --- | --- | --- | --- | --- | --- | --- |
| h01_bq_quota | hard | api_rate_limit | gcp_permission_denied | ✗ | ✓ | 0.65 | media |
| h02_kubernetes_evicted | hard | zombie_task | zombie_task | ✓ | ✓ | 0.60 | media |
| h03_disco_cheio | hard | desconhecido | desconhecido | ✓ | ✓ | 0.11 | baixa |
| h04_ssl | hard | desconhecido | pool_no_slots | ✗ | ✗ | 0.46 | baixa |
| h05_coluna_renomeada | easy | dataframe_missing_column | dataframe_missing_column | ✓ | ✓ | 0.73 | alta |
| h06_dataset_regiao | easy | bq_table_not_found | bq_table_not_found | ✓ | ✓ | 0.78 | alta |
| h07_mysql_gone | hard | db_connection_refused | db_connection_refused | ✓ | ✓ | 0.70 | media |
| h08_template_macro | easy | jinja_template_error | jinja_template_error | ✓ | ✓ | 0.91 | alta |

## Como ler

- **Top-1:** a primeira resposta é a causa certa.
- **Top-3:** a causa certa está entre as 3 opções mostradas na tela.
- **desconhecido:** falhas que a base não cobre. O certo é o assistente admitir que não reconhece.

## Limitações

- Todos os logs são sintéticos, escritos para o projeto, e o conjunto é pequeno.
- O conjunto de desenvolvimento foi usado para ajustar os padrões, então o resultado dele é otimista.
- Logs com duas falhas ao mesmo tempo não estão nos conjuntos.
