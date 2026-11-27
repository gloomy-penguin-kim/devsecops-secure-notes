#### The SecureNotes CI/CD pipeline is implemented using GitHub Actions and is triggered by pushes to the main branch and pull requests targeting main.

#### There are two parts to CI.yml: 
- **build-test:** checksout the repository, sets up python, installs dependencies, checks python syntax with compileall and then runs the application tests 
- **deploy:** after a successful build-test, it authenticates with AWS via OIDC credentials and uses the github-actions-deploy2 IAM role. 
	- permissions re restricted to contents: read and requring an id-token to write 

#### SAST.yml
- Examines code and configuration for insecure programming practices.
- This introduces Semgrep to perform Static Application Security Testing (SAST) automatically in Github Actions.  
- Without actually running the application, SAST examines source code and configurationf iles to look for security weaknesses 
- It is pointed at .smegrep/custom-rules.yml 

#### SCA.yml 
- Examines third-party dependencies for known vulnerabilities.
- Trivy is used to scan application dependencies for known vulnerabilities and generate a CycloneDX Software Bill of Materials (SBOM).  This is uploaded as a Github Actions artifact.  
- This security gate fails when vulnerabilities are found.  
- Trivy was tested when the Python package PyYAML 5.3.1 was introduced to `requirements.txt` because it was effected by CVE-2020-14343 and would therefore be detected and cause the workflow to fail.  

#### Dependabot.yml 
- Configured to check weelky for dependency updates. 


#### Lab 6 Container Security
I selected python:3.13-slim instead of a distroless image to maintain compatibility with Python dependencies, PostgreSQL connectivity, TLS certificate verification, and shell-based troubleshooting.

The runtime image was hardened by:
- Implementing a multi-stage build.
- Running the application as a non-root user.
- Removing pip and its vulnerable vendored dependencies.
- Patching the vulnerable libzstd1 operating system package.
- Enforcing a read-only root filesystem.
- Dropping all Linux capabilities.
- Providing a temporary writable filesystem for Gunicorn.

The hardened image reduced disk usage from 277 MB to 264 MB and vulnerability findings from 231 to 224.


`python -c "import secrets; print(secrets.token_hex(32))"`

`flask --app app init-db`
`flask --app app run`


- build the ap 
`docker build -t secure-notes .`

- test out the database connection
`docker run --rm --env-file .env secure-notes flask --app app init-db`

- run the app 
`docker run --rm -p 127.0.0.1:5000:5000 --env-file .env secure-notes`

- run semgrep witin docker locally 
`docker run --rm -v "${PWD}:/src" -w /src semgrep/semgrep semgrep --config auto --config .semgrep/custom-rules.yml --error .`

- run trivy within docker locally 
`docker run --rm -v "${PWD}:/src" aquasec/trivy:0.76.2 fs --scanners vuln --severity CRITICAL --exit-code 1 /src` 

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

- test login of the user
```powershell 
$result = Invoke-RestMethod `
    -Uri http://localhost:5000/login `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        username = "alice"
        password = "local-test-password"
    } | ConvertTo-Json)

$token = $result.access_token

$headers = @{
    Authorization = "Bearer $token"
}
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

