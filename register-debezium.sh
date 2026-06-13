#!/bin/bash

curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "crm-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "postgres",
      "database.port": "5432",
      "database.user": "postgres",
      "database.password": "password",
      "database.dbname": "bionicpro",
      "database.server.name": "crm",
      "plugin.name": "pgoutput",
      "slot.name": "crm_slot",
      "table.include.list": "public.clients,public.telemetry",
      "topic.prefix": "crm",
      "key.converter": "org.apache.kafka.connect.json.JsonConverter",
      "value.converter": "org.apache.kafka.connect.json.JsonConverter",
      "value.converter.schemas.enable": false
    }
  }'