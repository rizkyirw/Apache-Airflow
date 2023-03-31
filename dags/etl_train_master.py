from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
import requests
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 29),
    'retries': 1
}

dag = DAG(
    'api_to_mysql',
    default_args=default_args,
    schedule_interval='@daily',
)

def extract_api():
    url = 'https://api.example.com/data'
    response = requests.get(url)
    data = json.loads(response.text)
    return data

def transform_data(data):
    transformed_data = []
    for item in data:
        transformed_item = {
            'id': item['id'],
            'name': item['name'],
            'value': item['value']
        }
        transformed_data.append(transformed_item)
    return transformed_data

def load_to_mysql():
    mysql_hook = MySqlHook(mysql_conn_id='your_mysql_connection_id')
    data = transform_data(extract_api())
    for item in data:
        query = f"INSERT INTO your_table_name (id, name, value) VALUES ({item['id']}, '{item['name']}', {item['value']})"
        mysql_hook.run(query)

extract_task = PythonOperator(
    task_id='extract_api_data',
    python_callable=extract_api,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_api_data',
    python_callable=transform_data,
    op_kwargs={'data': '{{ ti.xcom_pull(task_ids="extract_api_data") }}'},
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data_to_mysql',
    python_callable=load_to_mysql,
    dag=dag,
)

extract_task >> transform_task >> load_task