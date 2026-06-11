# Задание 1
### Задача 1. Предложите архитектурное решение и доработайте диаграмму C4 для управления учётными данными пользователя.
[Диаграмма C4](BionicPRO_C4_model.drawio.xml)
### Задача 2. Улучшите безопасность существующего приложения, заменив Code Grant на PKCE.
[1](keycloak/realm-export.json) [2](docker-compose.yaml) [3](frontend/src/App.tsx)
### Задача 3. Обеспечьте безопасное получение и хранение access-и refresh-токенов.
[bionicpro-auth](bionicpro-auth)
### Задача 4. Добавьте LDAP для возможности получения данных о пользователях представительства BionicPRO в другой стране.
[ldap](ldap)
### Задача 5. Настройте MFA.
[realm-export](keycloak/realm-export.json)
### Задача 6. Добавьте OAuth 2.0 от Яндекс ID.
[realm-export](keycloak/realm-export.json)

# Задание 2
### Задача 1. Создать архитектуру решения для подготовки и получения отчётов.
[Диаграмма C4](BionicPRO_C4_model_airflow.drawio.xml)
### Задача 2. Разработать Airflow DAG и настроить его на запуск по расписанию.
[airflow](airflow)
### Задача 3. Создайте бэкенд-часть приложения для API.
[bionicpro-reports](bionicpro-reports)
### Задача 4. Реализуйте ограничение доступа к эндпоинту отчётности.
[bionicpro-reports](bionicpro-reports)
### Задача 5. Добавьте в UI кнопку получения отчёта и вызова эндпоинта его генерации.
[UI](frontend/src/components/ReportPage.tsx)