`python -c "import secrets; print(secrets.token_hex(32))"`

`flask --app app init-db`
`flask --app app run`


- build the ap 
`docker build -t secure-notes .`

- test out the database connection
`docker run --rm --env-file .env secure-notes flask --app app init-db`

- run the app 
`docker run --rm -p 127.0.0.1:5000:5000 --env-file .env secure-notes`

- test an api point 
`Invoke-RestMethod http://localhost:5000/health`

- make a test user 
```powershell 
Invoke-RestMethod `
    -Uri http://localhost:5000/register `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        username = "alice"
        password = "local-test-password"
    } | ConvertTo-Json)
```

- verify the tables are correct
```sql
SELECT table_name,
       column_name,
       data_type,
       is_nullable,
       column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('users', 'notes')
ORDER BY table_name, ordinal_position;
```

- view the users 
```sql
SELECT u.id AS user_id,
       u.username,
       n.id AS note_id,
       n.content,
       n.created_at
FROM users u
LEFT JOIN notes n
    ON u.id = n.user_id
ORDER BY u.id, n.created_at;
```

- verify your indexes 
```sql 
SELECT tablename,
       indexname,
       indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('users', 'notes');
```

- to reset the data during testing
```sql
TRUNCATE TABLE notes, users RESTART IDENTITY;
```

